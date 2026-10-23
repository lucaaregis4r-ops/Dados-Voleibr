"""Standalone scouting interface; the live server uses the same payload."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import base64
import os
from cbv.config import BASE_DIR
from cbv.database.repository import default_repo
from cbv.analysis.scouting import aggregate_cohort, metric_values, enrich_record, METRICS, VERSION
from cbv.analysis.temporal import walk_forward, evaluation

PUBLISH_DIR=Path(os.getenv('CBV_PUBLISH_DIR',BASE_DIR))
EXPORTS_DIR = PUBLISH_DIR/'exports'
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


def generate_dashboard_data(competition=None,include_atlas=True):
    with default_repo.get_connection() as conn:
        from cbv.analysis.atlas import load_atlas
        atlas=load_atlas(conn) if include_atlas else dict(rows=[],coverage={},sources=[],validations=[])
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
        if include_atlas:
            from cbv.analysis.atlas import summarize_team
            from cbv.analysis.rally_models import enrich_temporal
            from cbv.analysis.expected_attack import walk_forward_attack
            rally_rows=[r for r in atlas['rows'] if r['match_id'] in ids]
            c['rally_model']=enrich_temporal(mm,rally_rows)
            c['expected_attack']=walk_forward_attack(mm,rr)
            c['atlas_teams']={t['team']:summarize_team(rally_rows,t['team']) for t in c['teams']}
            from cbv.analysis.volume_distribution import estimate_distributions
            for name,summary in c['atlas_teams'].items():summary['distribution_model']=estimate_distributions(rally_rows,pp,name)
            for summary in c['atlas_teams'].values():
                summary['serve_runs'].pop('runs',None)
                for rotation in summary['rotations']:
                    for metric in ('so','bp'):
                        # Competition reference uses all covered rallies, independently of team.
                        outcomes=[]
                        for r in rally_rows:
                            for side in ('home','away'):
                                if r.get(side+'_rotation')==rotation['position'] and (r['serving_side']==side)==(metric=='bp'):
                                    outcomes.append(r['winner_side']==side)
                        avg=100*sum(outcomes)/len(outcomes) if outcomes else None
                        rotation[metric+'_delta_competition']=rotation[metric]['value']-avg if rotation[metric]['n'] and avg is not None else None
            rally_fields=['set_number','rally_number','score_home_before','score_away_before','score_home_after','score_away_after',
                'serving_side','winner_side','home_rotation','away_rotation','home_lineup','away_lineup','home_lineup_confidence','away_lineup_confidence',
                'wp_before','wp_after','wpa','leverage','expected_home','crunch','super_crunch','pressure_band']
            c['coverage']=dict(rotation_matches=len({r['match_id'] for r in rally_rows if r.get('home_rotation') and r.get('away_rotation')}),
                lineup_matches=len({r['match_id'] for r in rally_rows if r.get('home_lineup_confidence')=='RECONSTRUCTED_HIGH' and r.get('away_lineup_confidence')=='RECONSTRUCTED_HIGH' and r.get('home_lineup_names') and r.get('away_lineup_names')}))
            c['rally_fields']=rally_fields
            c['rallies']={str(mid):[[r.get(k) for k in rally_fields] for r in rally_rows if r['match_id']==mid] for mid in sorted({r['match_id'] for r in rally_rows})}
            c['atlas_validations']=[v for v in atlas['validations'] if v['match_id'] in ids]
            c['atlas_attempts']=[v for v in atlas.get('attempts',[]) if v['match_id'] in ids]
            c['source_snapshots']=[v for v in atlas['sources'] if v['match_id'] in ids]
            c['match_details']=build_match_details(ids,match_rows,match_players,set_rows)
        predictions,history,weights,ntrain=walk_forward(mm,rr)
        if include_atlas:
            from cbv.analysis.challengers import evaluate_intercept
            c['challenger']=evaluate_intercept(mm,rr)
            from cbv.analysis.opponent_ratings import evaluate_ratings
            c['opponent_ratings']=evaluate_ratings(mm,rr)
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
        if include_atlas:
            from cbv.analysis.model_registry import record_run,persist_rally_predictions
            with default_repo.get_connection() as model_conn:
                dates=sorted({str(m['date'])[:10] for m in mm if m.get('date')})
                window=[dates[0],dates[-1]] if dates else None
                baseline_run=record_run(model_conn,'logistic-l2-v1',c['id'],window,
                    ['so','bp','eff','pos_rec','neg_rec','trans','recent_win_difference'],
                    dict(weights=c['model_weights'],penalty=2.,scale=20,intercept=False),ntrain,len(predictions),c['evaluation'],'MODELADO')
                if rally_rows:
                    rally_run=record_run(model_conn,c['rally_model']['model_version'],c['id'],window,
                        ['team','serve_receive','score_state'],dict(prior_strength=30,global_prior='Jeffreys (k+.5)/(n+1)',runs=c['rally_model']['runs']),
                        len({r['match_id'] for r in rally_rows}),len({r['match_id'] for r in rally_rows if r.get('expected_home') is not None}),c['rally_model']['candidate'],'EXPERIMENTAL')
                    persist_rally_predictions(model_conn,rally_rows,rally_run)
                    c['rally_model']['run_id']=rally_run
                for phase,result in c['opponent_ratings'].items():
                    result['run_id']=record_run(model_conn,result['model_version'],c['id']+'|'+phase,window,
                        ['team','opponent'],result['parameters'],result['training_matches'],result['candidate']['matches'],result['candidate'],'EXPERIMENTAL')
                c['challenger']['run_id']=record_run(model_conn,c['challenger']['model_version'],c['id'],window,
                    c['challenger']['features'],dict(penalty=2.,intercept=True),ntrain,c['challenger']['candidate']['total_matches'],c['challenger']['candidate'],'EXPERIMENTAL')
                for name,summary in c['atlas_teams'].items():
                    distributions=summary.get('distribution_model',[])
                    if distributions:
                        summary['distribution_run_id']=record_run(model_conn,'lineup-volume-prior-v1',c['id']+'|'+name,window,
                            ['cohort_attack_volume','observed_modal_lineup','rotation'],dict(distributions=distributions,pass_effect=None),
                            max(m['volume_match_count'] for m in distributions),0,{},'EXPERIMENTAL')
                    result=summary['contextual_effect']
                    if result['parameters']:
                        team_dates=sorted({r['date'] for r in rally_rows if name in (r['home_team'],r['away_team']) and r.get('date')})
                        result['run_id']=record_run(model_conn,result['model_version'],c['id']+'|'+name,
                            [team_dates[0],team_dates[-1]] if team_dates else None,result['features'],result['parameters'],
                            result['training_matches'],result['candidate']['matches'],result['candidate'],'EXPERIMENTAL')
                c['baseline_run_id']=baseline_run
        c['upcoming']=[u for u in upcoming if tuple(u.get(k) for k in ('competition','category','gender','season'))==key]
        cohorts.append(c)
    cohorts.sort(key=lambda c:(c['competition']=='SUPERLIGA',str(c['season']),c['gender']=='feminino'),reverse=True)
    source_by_id={p['match_id']:p for p in provenance}
    for c in cohorts:
        for m in c['matches']:
            m['provenance']=source_by_id.get(m['match_id'])
    return dict(cohorts=cohorts, generated_at=datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),data_version='atlas-1.0',legacy_data_version=VERSION,definitions=definitions,metric_registry=__import__('cbv.metrics.registry',fromlist=['catalog']).catalog(),atlas_coverage=atlas['coverage'],
                kpis=dict(matches=sum(len(c['matches']) for c in cohorts),sets=sets,teams=len({t['team'] for c in cohorts for t in c['teams']})),
                # Compatibility with consumers of the previous data endpoint.
                summary={'sideout_breakpoint':[dict(team=t['team'],**t['metrics']['so']) for c in cohorts for t in c['teams']]},
                dossiers={t['team']:{'team':t['team'],'games':t['games']} for c in cohorts for t in c['teams']})


def build_dashboard_html(data):
    from cbv.metrics.registry import REGISTRY,catalog
    data['metric_registry']=catalog()
    for cohort in data.get('cohorts',[]):
        groups=[cohort.get('metrics',{})]
        for team in cohort.get('teams',[]):
            groups.append(team.get('metrics',{}))
            groups.extend(a.get('metrics',{}) for a in team.get('athletes',[]))
        for metrics in groups:
            for key,metric in metrics.items():
                if key in REGISTRY:metric['formula']=REGISTRY[key].formula
    template=(Path(__file__).parent/'templates'/'scouting.html').read_text(encoding='utf-8')
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    fonts = []
    for font in sorted((Path(__file__).parent/'templates'/'fonts').glob('*.woff2')):
        if not font.name.startswith(('inter-', 'roboto-mono-')):
            continue
        family = 'Inter' if font.name.startswith('inter-') else 'Roboto Mono'
        weight = font.stem.rsplit('-', 1)[1]
        encoded = base64.b64encode(font.read_bytes()).decode('ascii')
        fonts.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};font-display:swap;src:url(data:font/woff2;base64,{encoded}) format('woff2')}}")
    return template.replace('__SCOUTING_DATA__',payload).replace('__FONT_CSS__', ''.join(fonts)).replace('__ATLAS_CSS__',(Path(__file__).parent/'templates/atlas.css').read_text()).replace('__ATLAS_JS__',(Path(__file__).parent/'templates/atlas.js').read_text())


def export_dashboard_html(target_file=DEFAULT_HTML_PATH):
    target_file=Path(target_file); target_file.parent.mkdir(parents=True,exist_ok=True)
    data=generate_dashboard_data()
    html=build_dashboard_html(data)
    from cbv.export.atlas_export import export_atlas
    with default_repo.get_connection() as conn:export_atlas(data,EXPORTS_DIR,conn)
    target_file.write_text(html,encoding='utf-8')
    for p in (PUBLISH_DIR/'index.html',PUBLISH_DIR/'docs'/'index.html'):
        p.parent.mkdir(parents=True,exist_ok=True); p.write_text(html,encoding='utf-8')
    return target_file
