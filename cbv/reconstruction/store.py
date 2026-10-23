"""Additive Atlas tables; replace a match only after its reconstruction passes gates."""
import json
from pathlib import Path
from cbv.storage.raw import RawStore,utcnow
from cbv.parser.scoresheet import parse_scoresheet,parse_libero_report,parse_setter_markers
from cbv.reconstruction.rallies import rebuild_from_scoresheet,reconcile
from cbv.reconstruction.lineups import apply_positions

VERSION='atlas-reconstruction-1.0'


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
    from cbv.parser.match_report import normalize_team_name
    sheet=parse_scoresheet(sheet_path,mid)
    target={normalize_team_name(match['home_team']):'home',normalize_team_name(match['away_team']):'away'}
    mapping={letter:target.get(normalize_team_name(name)) for letter,name in sheet['team_names'].items()}
    if set(mapping.values())!={'home','away'}:raise ValueError('Equipes da súmula divergem do Match Report')
    sets=[dict(zip(('set_number','home_points','away_points'),r)) for r in conn.execute('SELECT set_number,home_points,away_points FROM sets WHERE match_id=? ORDER BY set_number',[mid]).fetchall()]
    rallies,events=rebuild_from_scoresheet(sheet,mapping,sets)
    markers=parse_setter_markers(report_path,match['home_team'],match['away_team'])
    libero_path=store.cached('libero_report');libero=parse_libero_report(libero_path,mid) if libero_path else None
    segments,warnings=apply_positions(rallies,sheet,events,mapping,{'home':markers.get(match['home_team'],{}),'away':markers.get(match['away_team'],{})},libero)
    validation=reconcile(rallies,sets)
    validation.update(source_hashes={k:v.get('sha256') for k,v in store.manifest['sources'].items()},events=events,coverage=sheet['coverage'],lineup_warnings=warnings)
    if warnings:validation['status']='VALID_WITH_WARNINGS'
    if validation['status']=='FAILED':return validation
    conn.begin()
    try:
        conn.execute('DELETE FROM rallies WHERE match_id=?',[mid]);conn.execute('DELETE FROM lineup_segments WHERE match_id=?',[mid])
        names=['rally_id','match_id','set_number','rally_number','serving_team','receiving_team','winner_team','rotation_home','rotation_away',
            'score_home_before','score_away_before','score_home_after','score_away_after','home_rotation','away_rotation',
            'home_setter_position','away_setter_position','is_breakpoint','is_sideout','rotation_source','rotation_confidence','payload','data_version']
        values=[]
        for r in rallies:
            r.update(serving_team=match[r['serving_side']+'_team'],receiving_team=match[r['receiving_side']+'_team'],winner_team=match[r['winner_side']+'_team'],
                rotation_home=r['home_rotation'],rotation_away=r['away_rotation'],payload=json.dumps(r,ensure_ascii=False,allow_nan=False),data_version=VERSION)
            values.append([r.get(k) for k in names])
        conn.executemany('INSERT INTO rallies ('+','.join(names)+') VALUES ('+','.join('?' for _ in names)+')',values)
        if segments:conn.executemany('INSERT INTO lineup_segments VALUES (?,?,?)',[[mid,i,json.dumps(s,ensure_ascii=False)] for i,s in enumerate(segments)])
        conn.execute('INSERT OR REPLACE INTO validation_reports VALUES (?,?,?,?)',[mid,validation['status'],json.dumps(validation,ensure_ascii=False),utcnow()])
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
