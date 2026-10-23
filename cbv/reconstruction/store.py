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
    existing={r[1] for r in conn.execute("PRAGMA table_info('rallies')").fetchall()}
    for name,kind in fields.items():
        if name not in existing:conn.execute(f'ALTER TABLE rallies ADD COLUMN {name} {kind}')


def reconstruct_match(conn,raw_root,match):
    mid=match['match_id'];store=RawStore(raw_root,mid)
    for kind,metadata in store.manifest['sources'].items():
        conn.execute('INSERT OR REPLACE INTO source_snapshots VALUES (?,?,?)',[mid,kind,json.dumps(metadata)])
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
        return ''.join(c for c in unicodedata.normalize('NFD',normalize_team_name(name)) if unicodedata.category(c)!='Mn').upper()
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
        if segments:conn.executemany('INSERT INTO lineup_segments VALUES (?,?,?)',[[mid,i,json.dumps(s,ensure_ascii=False)] for i,s in enumerate(segments)])
        conn.execute('INSERT OR REPLACE INTO validation_reports VALUES (?,?,?,?)',[mid,validation['status'],json.dumps(validation,ensure_ascii=False),utcnow()])
        store.manifest['sources']['scoresheet']['parser_version']=sheet['parser_version']
        store._save()
        conn.commit()
    except Exception:
        conn.rollback();raise
    return dict(status=validation['status'],rallies=len(rallies),rotations=sum(r['home_rotation'] is not None and r['away_rotation'] is not None for r in rallies),lineup_warnings=warnings)


def rebuild_all(conn,raw_root,competition=None,season=None,limit=None):
    initialize(conn)
    names=['match_id','home_team','away_team'];sql='SELECT match_id,home_team,away_team FROM matches WHERE validation_status=\'VALID\'';args=[]
    if competition:sql+=' AND lower(competition)=lower(?)';args.append(competition)
    if season:sql+=' AND season=?';args.append(season)
    sql+=' ORDER BY match_id DESC'
    if limit:sql+=' LIMIT ?';args.append(limit)
    matches=[dict(zip(names,r)) for r in conn.execute(sql,args).fetchall()];summary={}
    for match in matches:
        try:report=reconstruct_match(conn,raw_root,match)
        except Exception as exc:report=dict(status='FAILED',reason=f'{type(exc).__name__}: {exc}')
        conn.execute('INSERT OR REPLACE INTO reconstruction_attempts VALUES (?,?,?,?)',[match['match_id'],report['status'],json.dumps(report,ensure_ascii=False),utcnow()])
        summary[report['status']]=summary.get(report['status'],0)+1
    return summary
