"""Additive Atlas tables; replace a match only after its reconstruction passes gates."""
import json
from pathlib import Path
from cbv.storage.raw import RawStore,utcnow
from cbv.parser.scoresheet import parse_scoresheet,parse_libero_report,parse_setter_markers
from cbv.reconstruction.rallies import rebuild_from_scoresheet,reconcile
from cbv.reconstruction.lineups import apply_positions

VERSION='atlas-reconstruction-1.2'


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS source_snapshots(match_id BIGINT,source_type VARCHAR,metadata JSON,PRIMARY KEY(match_id,source_type));
    CREATE TABLE IF NOT EXISTS validation_reports(match_id BIGINT PRIMARY KEY,status VARCHAR,report JSON,updated_at VARCHAR);
    CREATE TABLE IF NOT EXISTS lineup_segments(match_id BIGINT,segment_number INTEGER,payload JSON,PRIMARY KEY(match_id,segment_number));
    CREATE TABLE IF NOT EXISTS reconstruction_attempts(match_id BIGINT PRIMARY KEY,status VARCHAR,report JSON,attempted_at VARCHAR);''')
    # Existing columns and readers remain supported. Explicit aliases are filled together.
    fields={'score_home_after':'INTEGER','score_away_after':'INTEGER','home_rotation':'INTEGER','away_rotation':'INTEGER',
        'home_setter_position':'INTEGER','away_setter_position':'INTEGER','is_breakpoint':'BOOLEAN','is_sideout':'BOOLEAN',
        'rotation_source':'VARCHAR','rotation_confidence':'VARCHAR','score_pressure':'DOUBLE','leverage':'DOUBLE',
        'wp_before':'DOUBLE','wp_after':'DOUBLE','wpa':'DOUBLE','payload':'JSON','data_version':'VARCHAR'}
    conn.execute("""CREATE OR REPLACE VIEW lineups AS SELECT match_id,segment_number,
        payload->>'lineup_id' AS lineup_id,CAST(payload->>'set_number' AS INTEGER) AS set_number,
        CAST(payload->>'start_rally' AS INTEGER) AS start_rally,CAST(payload->>'end_rally' AS INTEGER) AS end_rally,
        payload->'players' AS players,CAST(payload->>'setter' AS INTEGER) AS setter,
        CAST(payload->>'rotation' AS INTEGER) AS rotation,payload->>'team_side' AS team_side,
        payload->>'confidence' AS confidence FROM lineup_segments""")
    existing={r[1] for r in conn.execute("PRAGMA table_info('rallies')").fetchall()}
    for name,kind in fields.items():
        if name not in existing:conn.execute(f'ALTER TABLE rallies ADD COLUMN {name} {kind}')


def reconstruct_match(conn,raw_root,match,update_sources=True):
    mid=match['match_id'];store=RawStore(raw_root,mid)
    if update_sources:
        conn.begin()
        try:
            conn.executemany('INSERT OR REPLACE INTO source_snapshots VALUES (?,?,?)',[[mid,kind,json.dumps(metadata)] for kind,metadata in store.manifest['sources'].items()])
            conn.commit()
        except Exception:
            conn.rollback();raise
    sheet_path=store.cached('scoresheet');report_path=store.cached('match_report')
    if not sheet_path or not report_path:
        return dict(status='PARTIAL',reason='Súmula ou Match Report indisponível')
    from cbv.parser.scoresheet import PARSER_VERSION
    import hashlib
    signature=hashlib.sha256(json.dumps(dict(sources={k:v.get('sha256') for k,v in store.manifest['sources'].items()},parser=PARSER_VERSION,reconstruction=VERSION),sort_keys=True).encode()).hexdigest()
    previous=conn.execute('SELECT report FROM validation_reports WHERE match_id=?',[mid]).fetchone()
    if previous:
        cached=json.loads(previous[0])
        count=conn.execute('SELECT count(*) FROM rallies WHERE match_id=?',[mid]).fetchone()[0]
        if cached.get('input_signature')==signature and count==cached.get('rally_count'):
            return dict(status=cached['status'],rallies=count,cached=True,lineup_warnings=cached.get('lineup_warnings',[]))
    from cbv.parser.match_report import normalize_team_name
    import unicodedata
    def identity(name):
        normalized=' '.join(''.join(c for c in unicodedata.normalize('NFD',normalize_team_name(name)) if unicodedata.category(c)!='Mn').upper().split())
        aliases={'BRASILIA VOLEI / BRB':'BRASILIA VOLEI','PRAIA CLUBE UBERLANDIA VOLEI':'PRAIA CLUBE UBERLANDIA','VOLEI GUARULHOS BATEUBET':'VEDACIT VOLEI GUARULHOS'}
        return aliases.get(normalized,normalized)
    sheet=parse_scoresheet(sheet_path,mid)
    target={identity(match['home_team']):'home',identity(match['away_team']):'away'}
    mapping={letter:target.get(identity(name)) for letter,name in sheet['team_names'].items()}
    if set(mapping.values())!={'home','away'}:raise ValueError('Equipes da súmula divergem do Match Report')
    sets=[dict(zip(('set_number','home_points','away_points'),r)) for r in conn.execute('SELECT set_number,home_points,away_points FROM sets WHERE match_id=? ORDER BY set_number',[mid]).fetchall()]
    from cbv.parser.game_metadata import parse_game_metadata
    page_path=store.cached('game_page')
    metadata=parse_game_metadata(page_path.read_text(),mid) if page_path else None
    if metadata:
        if identity(metadata['home_team'])!=identity(match['home_team']) or identity(metadata['away_team'])!=identity(match['away_team']):
            raise ValueError('Identidades da página e do banco divergem')
        if sets and metadata['sets'] and sets!=metadata['sets']:
            raise ValueError('Placar por set da página diverge do relatório')
        if not sets and metadata['sets']:
            sets=metadata['sets'] # Independent observed source, not a fit to service-turn outcomes.
    if not sets:return dict(status='PARTIAL',reason='Sem placar por set independente para conciliar a súmula')
    rallies,events=rebuild_from_scoresheet(sheet,mapping,sets)
    pbp_path=store.cached('play_by_play');pbp_status='UNAVAILABLE';pbp_warning=None
    if pbp_path and pbp_path.suffix=='.json':
        from cbv.parser.play_by_play import parse_play_by_play
        try:observed=parse_play_by_play(json.loads(pbp_path.read_text()),mid)
        except ValueError as exc:
            pbp_status='UNSUPPORTED_SCHEMA';pbp_warning=str(exc)
        else:
            compared=['set_number','rally_number','score_home_before','score_away_before','score_home_after','score_away_after','serving_side','winner_side']
            if len(observed)!=len(rallies) or any(any(a[k]!=b[k] for k in compared) for a,b in zip(observed,rallies)):
                raise ValueError('Ponto a ponto e súmula divergem: não escolher silenciosamente uma fonte')
            for row,event in zip(rallies,observed):
                row.update(timestamp=event['timestamp'],observed_event=event['raw_event'],score_source='OBSERVED_STRUCTURED_PLAY_BY_PLAY')
            pbp_status='RECONCILED_OBSERVED'
    markers=parse_setter_markers(report_path,match['home_team'],match['away_team'])
    libero_path=store.cached('libero_report');libero=parse_libero_report(libero_path,mid) if libero_path else None
    segments,warnings=apply_positions(rallies,sheet,events,mapping,{'home':markers.get(match['home_team'],{}),'away':markers.get(match['away_team'],{})},libero)
    roster={}
    for team,jersey,name in conn.execute('SELECT team,player_number,player_name FROM player_match_stats WHERE match_id=?',[mid]).fetchall():
        roster.setdefault((team,jersey),set()).add(name)
    for row in rallies:
        for side in ('home','away'):
            identities=[roster.get((match[side+'_team'],jersey),set()) for jersey in row.get(side+'_lineup',[])]
            row[side+'_lineup_names']=[next(iter(names)) for names in identities] if len(identities)==6 and all(len(names)==1 for names in identities) else None
    validation=reconcile(rallies,sets)
    validation.update(input_signature=signature,rally_count=len(rallies),source_hashes={k:v.get('sha256') for k,v in store.manifest['sources'].items()},events=events,coverage=sheet['coverage'],lineup_warnings=warnings,set_reference='OBSERVED_GAME_PAGE_FLIGHT' if metadata else 'MATCH_REPORT',game_metadata=metadata)
    validation['play_by_play_status']=pbp_status
    if pbp_warning:validation['warnings'].append(pbp_warning)
    if warnings or pbp_warning:validation['status']='VALID_WITH_WARNINGS'
    if validation['status']=='FAILED':return validation
    conn.begin()
    try:
        if metadata and metadata['sets']:
            for score in sets:
                conn.execute('INSERT OR IGNORE INTO sets(match_id,set_number,home_points,away_points) VALUES (?,?,?,?)',[mid,score['set_number'],score['home_points'],score['away_points']])
        conn.execute('DELETE FROM rallies WHERE match_id=?',[mid]);conn.execute('DELETE FROM lineup_segments WHERE match_id=?',[mid])
        names=['rally_id','match_id','set_number','rally_number','serving_team','receiving_team','winner_team','rotation_home','rotation_away',
            'score_home_before','score_away_before','score_home_after','score_away_after','home_rotation','away_rotation',
            'home_setter_position','away_setter_position','is_breakpoint','is_sideout','rotation_source','rotation_confidence','payload','data_version']
        values=[]
        for r in rallies:
            r.update(serving_team=match[r['serving_side']+'_team'],receiving_team=match[r['receiving_side']+'_team'],winner_team=match[r['winner_side']+'_team'],
                rotation_home=r['home_rotation'],rotation_away=r['away_rotation'],payload=json.dumps(r,ensure_ascii=False,allow_nan=False),data_version=VERSION)
            values.append([r.get(k) for k in names])
        import pandas as pd
        frame=pd.DataFrame(values,columns=names)
        conn.register('atlas_rally_batch',frame)
        conn.execute('INSERT INTO rallies ('+','.join(names)+') SELECT '+','.join(names)+' FROM atlas_rally_batch')
        conn.unregister('atlas_rally_batch')
        if segments:
            segment_frame=pd.DataFrame([[mid,i,json.dumps(segment,ensure_ascii=False)] for i,segment in enumerate(segments)],columns=['match_id','segment_number','payload'])
            conn.register('atlas_lineup_batch',segment_frame)
            conn.execute('INSERT INTO lineup_segments SELECT * FROM atlas_lineup_batch')
            conn.unregister('atlas_lineup_batch')
        conn.execute('INSERT OR REPLACE INTO validation_reports VALUES (?,?,?,?)',[mid,validation['status'],json.dumps(validation,ensure_ascii=False),utcnow()])
        store.manifest['sources']['scoresheet']['parser_version']=sheet['parser_version']
        conn.execute('INSERT OR REPLACE INTO source_snapshots VALUES (?,?,?)',[mid,'scoresheet',json.dumps(store.manifest['sources']['scoresheet'])])
        store._save()
        conn.commit()
    except Exception:
        conn.rollback();raise
    return dict(status=validation['status'],rallies=len(rallies),rotations=sum(r['home_rotation'] is not None and r['away_rotation'] is not None for r in rallies),lineup_warnings=warnings)


def rebuild_all(conn,raw_root,competition=None,season=None,limit=None):
    initialize(conn)
    names=['match_id','home_team','away_team','validation_status'];sql='SELECT match_id,home_team,away_team,validation_status FROM matches WHERE 1=1';args=[]
    if competition:sql+=' AND lower(competition)=lower(?)';args.append(competition)
    if season:sql+=' AND season=?';args.append(season)
    sql+=' ORDER BY match_id DESC'
    if limit:sql+=' LIMIT ?';args.append(limit)
    matches=[dict(zip(names,r)) for r in conn.execute(sql,args).fetchall()];summary={};attempts=[]
    snapshots=[]
    for match in matches:
        store=RawStore(raw_root,match['match_id'])
        snapshots.extend([match['match_id'],kind,json.dumps(metadata)] for kind,metadata in store.manifest['sources'].items())
    if snapshots:
        conn.begin()
        try:
            conn.executemany('INSERT OR REPLACE INTO source_snapshots VALUES (?,?,?)',snapshots);conn.commit()
        except Exception:
            conn.rollback();raise
    for match in matches:
        try:
            if match['validation_status']!='VALID':
                report=dict(status='PARTIAL',reason='Match Report legado não validado; não alimentar reconstrução/modelos')
            else:report=reconstruct_match(conn,raw_root,match,update_sources=False)
        except Exception as exc:report=dict(status='FAILED',reason=f'{type(exc).__name__}: {exc}')
        attempts.append([match['match_id'],report['status'],json.dumps(report,ensure_ascii=False),utcnow()])
        summary[report['status']]=summary.get(report['status'],0)+1
    if attempts:
        conn.begin()
        try:
            conn.executemany('INSERT OR REPLACE INTO reconstruction_attempts VALUES (?,?,?,?)',attempts);conn.commit()
        except Exception:
            conn.rollback();raise
    return summary


def _validate_official(conn):
    """Compare independent report definitions without conflating credited/all points.

    These diagnostics never choose a rotation offset or fit a serving sequence.
    """
    from collections import defaultdict,Counter
    by_match=defaultdict(list)
    for row in conn.execute('SELECT match_id,serving_team,winner_team,home_rotation,away_rotation FROM rallies').fetchall():by_match[row[0]].append(row)
    names=['team','sideout_points','breakpoint_points','breakpoint_serves']+[f'p{i}_diff' for i in range(1,7)]
    for mid,home,away in conn.execute('SELECT match_id,home_team,away_team FROM matches').fetchall():
        previous=conn.execute('SELECT report FROM validation_reports WHERE match_id=?',[mid]).fetchone()
        if not previous or mid not in by_match:continue
        report=json.loads(previous[0]);checks=[];warnings=[];rows=by_match[mid]
        teams={team:dict(zip(names,row)) for row in conn.execute('SELECT '+','.join(names)+' FROM team_tactical_stats WHERE match_id=?',[mid]).fetchall() for team in [row[0]]}
        for side,team,column in [('home',home,3),('away',away,4)]:
            t=teams.get(team)
            if not t:continue
            so=sum(r[2]==team and r[1]!=team for r in rows);bp=sum(r[2]==team and r[1]==team for r in rows);served=sum(r[1]==team for r in rows)
            errors=conn.execute('SELECT opponent_errors FROM team_match_stats WHERE match_id=? AND team=?',[mid,team]).fetchone()
            check=dict(team=team,definition='Report creditado exclui erro adversário; sequência contém todos os pontos',
                report_so=t['sideout_points'],report_bp=t['breakpoint_points'],scoreboard_so=so,scoreboard_bp=bp,
                report_serves=t['breakpoint_serves'],scoreboard_serves=served)
            if errors and errors[0] is not None and t['sideout_points'] is not None and t['breakpoint_points'] is not None:
                check['credited_plus_opponent_errors']=t['sideout_points']+t['breakpoint_points']+errors[0]
                check['scoreboard_points']=so+bp
                check['credited_identity_passed']=check['credited_plus_opponent_errors']==so+bp
                if not check['credited_identity_passed']:warnings.append('Contagens creditadas + erros adversários divergem do placar')
            if t['breakpoint_serves'] is not None and t['breakpoint_serves']!=served:warnings.append('Saques do relatório diferem de pontos de placar sacando; verificar evento administrativo ou fonte')
            if all(r[column] is not None for r in rows) and all(t.get(f'p{i}_diff') is not None for i in range(1,7)):
                balance=Counter()
                for r in rows:balance[r[column]]+=1 if r[2]==team else -1
                check['reconstructed_rotation_balance']=[balance[i] for i in range(1,7)]
                check['report_rotation_balance']=[t[f'p{i}_diff'] for i in range(1,7)]
                check['rotation_balance_passed']=check['reconstructed_rotation_balance']==check['report_rotation_balance']
                if not check['rotation_balance_passed']:warnings.append('Saldo de rotações diverge do relatório; posição usa marcador inicial independente, sem ajuste pelo resultado')
            checks.append(check)
        report['official_checks']=checks;report['official_warnings']=sorted(set(warnings))
        if warnings and report['status']=='VALID':report['status']='VALID_WITH_WARNINGS'
        conn.execute('UPDATE validation_reports SET status=?,report=? WHERE match_id=?',[report['status'],json.dumps(report,ensure_ascii=False),mid])


def validate_official(conn):
    conn.begin()
    try:
        _validate_official(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
