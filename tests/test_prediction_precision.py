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


def test_current_season_bayesian_shrinkage():
    """Validates that predictions prioritize the active season with empirical Bayes shrinkage."""
    from cbv.analysis.tactics import get_team_tactical_dossier

    # Active season team with games
    d_sada = get_team_tactical_dossier("SADA CRUZEIRO VÔLEI", season="2025-2026")
    assert d_sada is not None
    rec_sada = d_sada["record"]
    assert rec_sada["target_season"] == "2025-2026"
    assert rec_sada["current_season_games"] >= 15
    assert rec_sada["current_season_weight_pct"] >= 85.0
    assert rec_sada["is_current_season_driven"] is True

    # Active season team without games in 2025-2026 (calibrated from prior)
    d_pin = get_team_tactical_dossier("E.C. PINHEIROS", season="2025-2026")
    assert d_pin is not None
    rec_pin = d_pin["record"]
    assert rec_pin["current_season_games"] == 0
    assert rec_pin["current_season_weight_pct"] == 0.0
    assert rec_pin["prior_weight_pct"] == 100.0
    assert rec_pin["is_current_season_driven"] is False

    # Match prediction calibration payload
    pred = predict_matchup("SADA CRUZEIRO VÔLEI", "ITAMBÉ MINAS", season="2025-2026", include_evaluation=False)
    assert pred is not None
    prec = pred["precision"]
    assert "season_calibration" in prec
    calib = prec["season_calibration"]
    assert calib["target_season"] == "2025-2026"
    assert "SADA CRUZEIRO VÔLEI" in calib
    assert calib["SADA CRUZEIRO VÔLEI"]["current_weight_pct"] >= 85.0
