"""Unit and regression tests for Match Report parsing."""

from pathlib import Path
import pytest
from cbv.parser.match_report import parse_match_report_pdf

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "match_2590834.pdf"


@pytest.fixture(scope="module")
def parsed_match():
    assert FIXTURE_PDF.exists(), "match_2590834.pdf fixture must exist"
    return parse_match_report_pdf(FIXTURE_PDF, 2590834)


def test_match_id(parsed_match):
    assert parsed_match.match.match_id == 2590834


def test_extract_teams(parsed_match):
    assert parsed_match.match.home_team == "RIO DE JANEIRO"
    assert parsed_match.match.away_team == "MINAS GERAIS"
    assert parsed_match.match.home_sets == 1
    assert parsed_match.match.away_sets == 2


def test_set_scores(parsed_match):
    assert len(parsed_match.sets) == 3
    s1, s2, s3 = parsed_match.sets

    assert s1.set_number == 1
    assert s1.home_points == 19
    assert s1.away_points == 25
    assert s1.duration_minutes == 25
    assert s1.partial_scores == "1-8 8-16 13-21"

    assert s2.set_number == 2
    assert s2.home_points == 25
    assert s2.away_points == 19

    assert s3.set_number == 3
    assert s3.home_points == 13
    assert s3.away_points == 15


def test_extract_players(parsed_match):
    assert len(parsed_match.players) == 20
    rio_players = [p for p in parsed_match.players if p.team == "RIO DE JANEIRO"]
    minas_players = [p for p in parsed_match.players if p.team == "MINAS GERAIS"]

    assert len(rio_players) == 10
    assert len(minas_players) == 10

    # Test Arthur (Rio #1)
    arthur = next(p for p in rio_players if p.player_number == 1)
    assert arthur.player_name == "ARTHUR"
    assert arthur.is_libero is False
    assert arthur.points_total == 6
    assert arthur.serve_points == 5
    assert arthur.attack_points == 1

    # Test Libero Rafael (Rio #3)
    libero_rio = next(p for p in rio_players if p.player_number == 3)
    assert libero_rio.is_libero is True
    assert libero_rio.player_name == "RAFAEL"
    assert libero_rio.reception_attempts == 21

    # Test Matheus (Minas #9) - top scorer
    matheus = next(p for p in minas_players if p.player_number == 9)
    assert matheus.player_name == "MATHEUS"
    assert matheus.points_total == 18
    assert matheus.attack_points == 13
    assert matheus.block_points == 3
    assert matheus.serve_points == 2


def test_attack_totals(parsed_match):
    rio_team = next(t for t in parsed_match.teams if t.team == "RIO DE JANEIRO")
    minas_team = next(t for t in parsed_match.teams if t.team == "MINAS GERAIS")

    assert rio_team.attack_attempts == 64
    assert rio_team.attack_points == 28
    assert minas_team.attack_attempts == 54
    assert minas_team.attack_points == 25

    # Opponent errors check
    assert rio_team.opponent_errors == 16
    assert minas_team.opponent_errors == 22


def test_regression_exact_values(parsed_match):
    """Guarantees that re-running the parser always produces deterministic expected results."""
    assert parsed_match.validation_status == "VALID"
    assert len(parsed_match.validation_warnings) == 0

    # Total points sum
    rio_team = next(t for t in parsed_match.teams if t.team == "RIO DE JANEIRO")
    minas_team = next(t for t in parsed_match.teams if t.team == "MINAS GERAIS")

    assert rio_team.points_total == 41
    assert minas_team.points_total == 37
