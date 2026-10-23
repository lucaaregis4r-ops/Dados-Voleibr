"""Forecast validation tests assert correctness, never a desired accuracy target."""
import pytest
from cbv.analysis.predictions import predict_matchup, evaluate_prediction_model
from cbv.analysis.temporal import walk_forward, evaluation


def test_prediction_is_model_with_measured_validation():
    pred=predict_matchup('SADA CRUZEIRO VÔLEI','ITAMBÉ MINAS',season='2025-2026')
    assert pred is not None
    assert pred['metric_class']=='MODELO'
    assert sum(pred['probabilities'].values())==pytest.approx(100)
    precision=pred['precision']
    assert precision['ci_90'] is None
    assert precision['margin_of_error_pct'] is None
    ev=precision['validation']
    assert precision['brier_score']==ev['brier_score']
    assert precision['empirical_accuracy_pct']==ev['accuracy_pct']
    assert ev['total_matches']>0
    assert 0<=ev['brier_score']<=1
    assert ev['log_loss']>=0


def test_evaluation_has_strict_temporal_boundaries():
    ev=evaluate_prediction_model()
    assert ev['total_matches']==len(ev['predictions'])>0
    assert all(p['trained_through']<p['date'] for p in ev['predictions'])
    assert all(p['training_matches']>=20 for p in ev['predictions'])
    assert 0<=ev['calibration_error']<=1


def test_future_results_cannot_change_past_predictions():
    from cbv.export.html_dashboard import generate_dashboard_data
    from cbv.database.repository import default_repo
    from cbv.export.html_dashboard import records
    data=generate_dashboard_data()
    c=next(c for c in data['cohorts'] if c['evaluation']['total_matches']>10)
    with default_repo.get_connection() as conn:
        rr=records(conn,'SELECT t.*, s.* EXCLUDE(match_id, team), m.date FROM team_match_stats t JOIN matches m USING(match_id) LEFT JOIN team_tactical_stats s USING(match_id, team)')
    ids={m['match_id'] for m in c['matches']};rr=[r for r in rr if r['match_id'] in ids]
    baseline,_,_,_=walk_forward(c['matches'],rr)
    cutoff=baseline[len(baseline)//2]['date']
    changed=[dict(m,home_sets=m['away_sets'],away_sets=m['home_sets']) if m['date']>cutoff else dict(m) for m in c['matches']]
    after,_,_,_=walk_forward(changed,rr)
    assert [p for p in baseline if p['date']<=cutoff]==[p for p in after if p['date']<=cutoff]


def test_empty_validation_is_unavailable():
    ev=evaluation([])
    assert ev['total_matches']==0
    assert ev['brier_score'] is None
    assert ev['accuracy_pct'] is None
