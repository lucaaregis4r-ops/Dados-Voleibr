"""Unit tests for analytical metrics and rankings generation."""

import pytest
from cbv.analysis.metrics import (
    calc_attack_success_pct,
    calc_attack_efficiency,
    calc_ace_rate,
    calc_serve_error_rate,
    calc_ace_error_ratio,
    calc_per_set,
)
from cbv.analysis.rankings import (
    get_aggregated_player_stats,
    get_scoring_ranking,
    get_attack_ranking,
    get_block_ranking,
    get_serve_ranking,
)


def test_metrics_formulas():
    # Attack success
    assert calc_attack_success_pct(10, 20) == 50.0
    assert calc_attack_success_pct(0, 10) == 0.0
    assert calc_attack_success_pct(5, 0) is None
    assert calc_attack_success_pct(None, 10) is None

    # Attack efficiency
    # (points - errors - blocked) / attempts
    # (10 - 2 - 2) / 20 = 6 / 20 = 30.0%
    assert calc_attack_efficiency(10, 2, 2, 20) == 30.0
    assert calc_attack_efficiency(5, 2, 1, 0) is None

    # Ace rate
    assert calc_ace_rate(3, 15) == 20.0
    assert calc_ace_rate(0, 10) == 0.0
    assert calc_ace_rate(3, 0) is None

    # Serve error rate
    assert calc_serve_error_rate(3, 15) == 20.0

    # Ace/Error ratio
    assert calc_ace_error_ratio(4, 2) == 2.0
    assert calc_ace_error_ratio(3, 0) == 3.0
    assert calc_ace_error_ratio(None, 2) is None

    # Per set
    assert calc_per_set(15, 3) == 5.0
    assert calc_per_set(10, 0) is None


def test_rankings_queries():
    stats = get_aggregated_player_stats()
    assert len(stats) > 0

    scoring = get_scoring_ranking(limit=5)
    assert len(scoring) <= 5
    if len(scoring) > 1:
        assert scoring[0]["total_points"] >= scoring[1]["total_points"]

    attack = get_attack_ranking(min_attempts=5, limit=5)
    if attack:
        assert all(p["total_attack_attempts"] >= 5 for p in attack)
        if len(attack) > 1:
            assert attack[0]["attack_success_pct"] >= attack[1]["attack_success_pct"]

    block = get_block_ranking(limit=5)
    if block:
        if len(block) > 1:
            assert block[0]["total_blocks"] >= block[1]["total_blocks"]

    serve = get_serve_ranking(min_attempts=5, limit=5)
    if serve:
        assert all(p["total_serve_attempts"] >= 5 for p in serve)
