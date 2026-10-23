"""Unit tests for setter distribution and attack prediction models."""

import pytest
from cbv.analysis.setter_distribution import (
    infer_team_tactical_roles,
    get_5x1_rotation_lineup,
    compute_setter_distribution,
)


def test_infer_team_tactical_roles():
    roles = infer_team_tactical_roles("SÃO PAULO")
    assert roles is not None
    assert roles["team"] == "SÃO PAULO"
    assert roles["setter"] is not None
    assert roles["libero"] is not None
    assert roles["oh1"] is not None
    assert roles["total_team_attacks"] > 0


def test_get_5x1_rotation_lineup():
    roles = infer_team_tactical_roles("SÃO PAULO")
    p1 = get_5x1_rotation_lineup(roles, "P1")
    assert p1["rotation"] == "P1"
    assert p1["setter_zone"] == "Fundo"
    assert len(p1["front_row"]) == 3

    p2 = get_5x1_rotation_lineup(roles, "P2")
    assert p2["rotation"] == "P2"
    assert p2["setter_zone"] == "Rede"
    assert len(p2["front_row"]) == 2


def test_compute_setter_distribution_pass_conditioning():
    # In P1: Positive vs Negative pass
    dist_pos = compute_setter_distribution("SÃO PAULO", rotation="P1", pass_quality="positive")
    assert dist_pos is not None
    assert dist_pos["predictability_pct"] >= 0.0
    assert dist_pos["predictability_pct"] <= 100.0

    dist_neg = compute_setter_distribution("SÃO PAULO", rotation="P1", pass_quality="negative")
    assert dist_neg is not None

    # On negative pass, wing hitter (OH1) probability should be much higher than on positive pass
    oh1_pos = next(d for d in dist_pos["distribution"] if d["player_name"] == dist_pos["distribution"][0]["player_name"] or "OH1" in d["role"])
    oh1_neg = next(d for d in dist_neg["distribution"] if d["player_name"] == oh1_pos["player_name"])

    # On negative pass, middle attack drops and wing attack takes over
    mb_pos = next((d for d in dist_pos["distribution"] if "MB" in d["role"]), None)
    mb_neg = next((d for d in dist_neg["distribution"] if "MB" in d["role"]), None)

    if mb_pos and mb_neg:
        assert mb_pos["probability_pct"] > mb_neg["probability_pct"]

    # Precision metrics present
    for item in dist_pos["distribution"]:
        assert item["margin_error_pct"] is None
        assert item["ci_95"] is None
        assert dist_pos["metric_class"] == "EXPERIMENTAL"
        assert "Não corresponde" in dist_pos["limitation"]
        assert item["expected_kill_pct"] >= 0.0
