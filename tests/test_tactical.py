"""Unit tests for tactical data extraction and validation."""

from pathlib import Path
import pytest

from cbv.parser.match_report import parse_match_report_pdf
from cbv.parser.tactical import extract_tactical_data

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "match_2590834.pdf"


@pytest.fixture(scope="module")
def parsed_match():
    assert FIXTURE_PDF.exists(), "match_2590834.pdf fixture must exist"
    return parse_match_report_pdf(FIXTURE_PDF, 2590834)


def test_tactical_data_present(parsed_match):
    assert parsed_match.tactical is not None
    assert parsed_match.tactical.match_id == 2590834
    assert parsed_match.tactical.home_team == "RIO DE JANEIRO"
    assert parsed_match.tactical.away_team == "MINAS GERAIS"


def test_sideout_breakpoint_stats(parsed_match):
    home_so = parsed_match.tactical.home_tactics.sideout
    assert home_so.team == "RIO DE JANEIRO"
    assert home_so.receptions_total == 48
    assert home_so.sideout_points == 23
    assert home_so.sideout_rate == 2.09
    assert home_so.serves_total == 58
    assert home_so.breakpoint_points == 18
    assert home_so.breakpoint_rate == 3.22

    away_so = parsed_match.tactical.away_tactics.sideout
    assert away_so.team == "MINAS GERAIS"
    assert away_so.receptions_total == 44
    assert away_so.sideout_points == 19
    assert away_so.sideout_rate == 2.32
    assert away_so.serves_total == 58
    assert away_so.breakpoint_points == 18
    assert away_so.breakpoint_rate == 3.22


def test_setter_rotations(parsed_match):
    h_rot = parsed_match.tactical.home_tactics.rotations
    assert h_rot == {"p1": 3, "p2": 4, "p3": 1, "p4": -4, "p5": -3, "p6": -3}

    a_rot = parsed_match.tactical.away_tactics.rotations
    assert a_rot == {"p1": -2, "p2": 3, "p3": -3, "p4": 0, "p5": 4, "p6": 0}


def test_phase_attacks_k1_k2(parsed_match):
    h_tactics = parsed_match.tactical.home_tactics

    # K1+ (Positive reception attack)
    k1_pos = h_tactics.positive_reception_attack
    assert k1_pos.phase_name == "k1_positive_reception"
    assert k1_pos.attempts == 28
    assert k1_pos.points == 11
    assert k1_pos.points_pct == 39.0
    assert k1_pos.blocked == 4
    assert k1_pos.errors == 4
    assert k1_pos.efficiency_pct == 10.71

    # K1- (Negative reception attack)
    k1_neg = h_tactics.negative_reception_attack
    assert k1_neg.phase_name == "k1_negative_reception"
    assert k1_neg.attempts == 12
    assert k1_neg.points == 7
    assert k1_neg.points_pct == 58.0
    assert k1_neg.blocked == 1
    assert k1_neg.errors == 2
    assert k1_neg.efficiency_pct == 33.33

    # K2 (Transition counter-attack)
    k2 = h_tactics.transition_attack
    assert k2.phase_name == "k2_transition"
    assert k2.attempts == 24
    assert k2.points == 10
    assert k2.points_pct == 42.0
    assert k2.blocked == 3
    assert k2.errors == 1
    assert k2.efficiency_pct == 25.0

    # Total attacks equality: K1+ + K1- + K2 == Total Team Attacks
    total_phase_attempts = k1_pos.attempts + k1_neg.attempts + k2.attempts
    assert total_phase_attempts == 64


def test_set_tactical_breakdowns(parsed_match):
    sets = parsed_match.tactical.home_tactics.set_breakdowns
    assert len(sets) == 3

    s1, s2, s3 = sets
    assert s1.set_number == 1
    assert s1.serve_points_won + s1.attack_points_won + s1.block_points_won + s1.opponent_errors_won == 19
    assert s1.attack_total == 22

    assert s2.set_number == 2
    assert s2.serve_points_won + s2.attack_points_won + s2.block_points_won + s2.opponent_errors_won == 25
    assert s2.attack_total == 29

    assert s3.set_number == 3
    assert s3.serve_points_won + s3.attack_points_won + s3.block_points_won + s3.opponent_errors_won == 13
    assert s3.attack_total == 13

    # Total set attack sum matches total phase attempts
    assert s1.attack_total + s2.attack_total + s3.attack_total == 64


def test_competition_tactical_summary():
    from cbv.analysis.tactics import get_competition_tactical_summary

    summary = get_competition_tactical_summary()
    assert "sideout_breakpoint" in summary
    assert "phase_attacks" in summary
    assert "rotations" in summary
    assert "reception_targets" in summary
    assert "offensive_usage" in summary

    so_bp = summary["sideout_breakpoint"]
    assert len(so_bp) >= 10
    assert "SÃO PAULO" in so_bp["team"].values

    rot = summary["rotations"]
    assert len(rot) >= 10
    sp_rot = rot[rot["team"] == "SÃO PAULO"].iloc[0]
    assert sp_rot["total_diff"] > 0


def test_team_tactical_dossier():
    from cbv.analysis.tactics import get_team_tactical_dossier

    dossier = get_team_tactical_dossier("SÃO PAULO")
    assert dossier is not None
    assert dossier["team"] == "SÃO PAULO"
    assert dossier["record"]["games"] >= 5
    assert dossier["totals"]["so_pct"] > 50.0
    assert len(dossier["attackers"]) >= 3
    assert len(dossier["receivers"]) >= 2
