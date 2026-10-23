"""Standalone editorial scouting publication; the live server uses the same payload."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import base64
from cbv.config import BASE_DIR
from cbv.database.repository import default_repo
from cbv.analysis.scouting import aggregate_cohort, metric_values, enrich_record, METRICS, VERSION
from cbv.analysis.temporal import walk_forward, evaluation

EXPORTS_DIR = BASE_DIR/'exports'
DEFAULT_HTML_PATH = EXPORTS_DIR/'dashboard.html'


def records(conn, sql):
    frame = conn.execute(sql).fetchdf()
    return json.loads(frame.to_json(orient='records', date_format='iso'))


def build_match_details(ids, team_rows, player_rows, set_rows):
    """Presentation payload of existing observations, using the same metric functions."""
    def brief(metrics):
        return {k:{f:m[f] for f in ('value','n','numerator','ci')} for k,m in metrics.items()}
    details={str(mid):dict(teams={},players=[],sets=[]) for mid in ids}
    for row in team_rows:
        if row['match_id'] not in ids:
            continue
        details[str(row['match_id'])]['teams'][row['team']] = dict(
            metrics=brief(metric_values([enrich_record(dict(row))])),
            aces=row.get('serve_points'), serve_errors=row.get('serve_errors'),
            blocks=row.get('block_points'),
            rotations=[row.get(f'p{i}_diff') for i in range(1,7)])
    for row in player_rows:
        if row['match_id'] not in ids:
            continue
        metrics=metric_values([enrich_record(dict(row))])
        details[str(row['match_id'])]['players'].append(dict(
            name=row['player_name'],team=row['team'],games=1,
            points=row.get('points_total'),receptions=row.get('reception_attempts'),
            metrics=brief({k:metrics[k] for k in ('kill','eff','positive','rec_error')})))
    for row in set_rows:
        if row['match_id'] in ids:
            details[str(row['match_id'])]['sets'].append(row)
    return details


def generate_dashboard_data(competition=None):
    with default_repo.get_connection() as conn:
        matches = records(conn, 'SELECT * FROM matches ORDER BY date, match_id')
        rows = records(conn, '''SELECT t.*, s.* EXCLUDE(match_id, team), m.date FROM team_match_stats t
            JOIN matches m USING(match_id) LEFT JOIN team_tactical_stats s USING(match_id, team)
            WHERE m.validation_status = 'VALID' ''')
        players = records(conn, "SELECT p.* FROM player_match_stats p JOIN matches m USING(match_id) WHERE m.validation_status = 'VALID'")
        # Expose existing match records for the match screen; ingestion/schema stay unchanged.
        match_rows = records(conn, "SELECT t.*, s.* EXCLUDE(match_id, team) FROM team_match_stats t LEFT JOIN team_tactical_stats s USING(match_id, team)")
        match_players = records(conn, "SELECT * FROM player_match_stats")
        set_rows = records(conn, "SELECT * FROM sets ORDER BY match_id, set_number")
        upcoming = records(conn, 'SELECT * FROM upcoming_matches ORDER BY match_date, match_time')
        definitions = records(conn, 'SELECT * FROM metric_definitions ORDER BY metric_key')
        provenance = records(conn, 'SELECT * FROM match_provenance')
        sets = conn.execute('select count(*) from sets').fetchone()[0]
    grouped = defaultdict(list)
    for m in matches:
        if competition and competition!='ALL' and competition.upper() not in (str(m['competition']).upper(),f"{m['competition']}_{m['gender']}".upper()):
            continue
        grouped[(m['competition'],m['category'],m['gender'],m['season'])].append(m)
    cohorts=[]
    for key, mm in grouped.items():
        ids={m['match_id'] for m in mm}; rr=[r for r in rows if r['match_id'] in ids]
        pp=[p for p in players if p['match_id'] in ids]
        c=aggregate_cohort(mm,rr,pp)
        c['match_details']=build_match_details(ids,match_rows,match_players,set_rows)
        predictions,history,weights,ntrain=walk_forward(mm,rr)
        c.update(dict(id='|'.join(str(x or '') for x in key),competition=key[0],category=key[1],gender=key[2],season=key[3],evaluation=evaluation(predictions),model_weights=weights.tolist() if weights is not None else None,training_matches=ntrain))
        from cbv.analysis.temporal import feature_vector, probability
        c['model_matchups']=[]
        names=sorted(history)
        if weights is not None:
            for i,a in enumerate(names):
                for b in names[i+1:]:
                    vector=feature_vector(history[a],history[b]) if history[a] and history[b] else None
                    if vector is not None:
                        c['model_matchups'].append(dict(team_a=a,team_b=b,probability_a=probability(weights,vector)))
        c['upcoming']=[u for u in upcoming if tuple(u.get(k) for k in ('competition','category','gender','season'))==key]
        cohorts.append(c)
    cohorts.sort(key=lambda c:(c['competition']=='SUPERLIGA',str(c['season']),c['gender']=='feminino'),reverse=True)
    source_by_id={p['match_id']:p for p in provenance}
    for c in cohorts:
        for m in c['matches']:
            m['provenance']=source_by_id.get(m['match_id'])
    return dict(cohorts=cohorts, generated_at=datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),data_version=VERSION,definitions=definitions,
                kpis=dict(matches=sum(len(c['matches']) for c in cohorts),sets=sets,teams=len({t['team'] for c in cohorts for t in c['teams']})),
                # Compatibility with consumers of the previous data endpoint.
                summary={'sideout_breakpoint':[dict(team=t['team'],**t['metrics']['so']) for c in cohorts for t in c['teams']]},
                dossiers={t['team']:{'team':t['team'],'games':t['games']} for c in cohorts for t in c['teams']})


def build_dashboard_html(data):
    template=(Path(__file__).parent/'templates'/'scouting.html').read_text(encoding='utf-8')
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    fonts = []
    for font in sorted((Path(__file__).parent/'templates'/'fonts').glob('*.ttf')):
        if not font.name.startswith(('inter-', 'roboto-mono-')):
            continue
        family = 'Inter' if font.name.startswith('inter-') else 'Roboto Mono'
        weight = font.stem.rsplit('-', 1)[1]
        encoded = base64.b64encode(font.read_bytes()).decode('ascii')
        fonts.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};font-display:swap;src:url(data:font/ttf;base64,{encoded}) format('truetype')}}")
    return template.replace('__SCOUTING_DATA__',payload).replace('__FONT_CSS__', ''.join(fonts))


def export_dashboard_html(target_file=DEFAULT_HTML_PATH):
    target_file=Path(target_file); target_file.parent.mkdir(parents=True,exist_ok=True)
    html=build_dashboard_html(generate_dashboard_data())
    target_file.write_text(html,encoding='utf-8')
    for p in (BASE_DIR/'index.html',BASE_DIR/'docs'/'index.html'):
        p.parent.mkdir(parents=True,exist_ok=True); p.write_text(html,encoding='utf-8')
    return target_file
