"""Portable audit exports in addition to the self-contained site."""
import json
from pathlib import Path


def export_atlas(data,target,conn):
    target=Path(target);target.mkdir(parents=True,exist_ok=True)
    document=dict(data_version=data['data_version'],generated_at=data['generated_at'],metric_registry=data.get('metric_registry'),
        coverage=data.get('atlas_coverage'),cohorts=[dict(id=c['id'],teams=c.get('atlas_teams',{}),sources=c.get('source_snapshots',[]),
            attempts=c.get('atlas_attempts',[]),baseline_run_id=c.get('baseline_run_id'),rally_model=c.get('rally_model'),challenger=c.get('challenger'),
            opponent_ratings=c.get('opponent_ratings')) for c in data['cohorts']])
    (target/'atlas_metrics.json').write_text(json.dumps(document,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
    tables={r[0] for r in conn.execute('SHOW TABLES').fetchall()}
    if 'validation_reports' in tables:
        conn.execute('''SELECT r.* EXCLUDE(payload) FROM rallies r JOIN validation_reports v USING(match_id) JOIN reconstruction_attempts a USING(match_id)
            WHERE a.status IN ('VALID','VALID_WITH_WARNINGS') AND v.status IN ('VALID','VALID_WITH_WARNINGS') ORDER BY match_id,set_number,rally_number''').fetchdf().to_csv(target/'rallies.csv',index=False)
        conn.execute('SELECT * FROM source_snapshots ORDER BY match_id,source_type').fetchdf().to_json(target/'source_manifests.json',orient='records',force_ascii=False)
        conn.execute('SELECT * FROM validation_reports ORDER BY match_id').fetchdf().to_json(target/'validation_reports.json',orient='records',force_ascii=False)
    if 'model_runs' in tables:conn.execute('SELECT * FROM model_runs ORDER BY scope,model_version,trained_at').fetchdf().to_json(target/'model_runs.json',orient='records',force_ascii=False)
