"""Unit tests for match prediction and empirical precision metrics."""

import pytest
from cbv.analysis.predictions import predict_matchup, evaluate_prediction_model


def test_predict_matchup_precision_metrics():
    pred = predict_matchup("SÃO PAULO", "PARANÁ")
    assert pred is not None
    assert "probabilities" in pred
    assert "precision" in pred

    prec = pred["precision"]
    assert "margin_of_error_pct" in prec
    assert prec["margin_of_error_pct"] > 0.0
    assert "ci_90" in prec
    assert "empirical_accuracy_pct" in prec
    assert prec["empirical_accuracy_pct"] >= 70.0
    assert "brier_score" in prec
    assert 0.0 <= prec["brier_score"] <= 0.25

    # Check that probabilities sum to 100
    p_a = pred["probabilities"]["SÃO PAULO"]
    p_b = pred["probabilities"]["PARANÁ"]
    assert abs(p_a + p_b - 100.0) < 0.2


def test_evaluate_prediction_model():
    eval_res = evaluate_prediction_model()
    assert eval_res["total_matches"] > 0
    assert eval_res["accuracy_pct"] >= 70.0
    assert eval_res["brier_score"] > 0.0
    assert "calibration" in eval_res
    assert "50-60%" in eval_res["calibration"]
