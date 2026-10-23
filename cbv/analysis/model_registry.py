"""Content-addressed model runs; no silent replacement of the pre-match baseline."""
import hashlib,json
from cbv.storage.raw import utcnow


def record_run(conn,model_version,scope,training_window,features,parameters,training_matches,evaluation_matches,evaluation,metric_class):
    conn.execute('''CREATE TABLE IF NOT EXISTS model_runs(
        run_id VARCHAR PRIMARY KEY,model_version VARCHAR,scope VARCHAR,trained_at VARCHAR,
        training_window JSON,features JSON,parameters JSON,training_matches INTEGER,evaluation_matches INTEGER,
        brier DOUBLE,log_loss DOUBLE,calibration JSON,metric_class VARCHAR)''')
    content=dict(model_version=model_version,scope=scope,training_window=training_window,features=features,parameters=parameters,
        training_matches=training_matches,evaluation_matches=evaluation_matches,evaluation=evaluation,metric_class=metric_class)
    run_id=hashlib.sha256(json.dumps(content,sort_keys=True,allow_nan=False).encode()).hexdigest()
    conn.execute('INSERT OR IGNORE INTO model_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',[
        run_id,model_version,scope,utcnow(),json.dumps(training_window),json.dumps(features),json.dumps(parameters),training_matches,evaluation_matches,
        evaluation.get('brier',evaluation.get('brier_score')),evaluation.get('log_loss'),json.dumps(evaluation.get('calibration')),metric_class])
    return run_id


def persist_rally_predictions(conn,rows,run_id):
    if not rows:return
    import pandas as pd
    fields=['rally_id','wp_before','wp_after','wpa','leverage']
    frame=pd.DataFrame([{k:r.get(k) for k in fields} for r in rows])
    conn.register('atlas_model_predictions',frame)
    conn.execute('''UPDATE rallies SET wp_before=p.wp_before,wp_after=p.wp_after,wpa=p.wpa,leverage=p.leverage
        FROM atlas_model_predictions p WHERE rallies.rally_id=p.rally_id''')
    conn.unregister('atlas_model_predictions')
