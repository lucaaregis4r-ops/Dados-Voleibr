"""Unit tests for MatchValidator."""

from copy import deepcopy
import pytest
from cbv.parser.match_report import parse_match_report_pdf
from cbv.validation.match_validator import MatchValidator
from tests.test_match_report import FIXTURE_PDF


@pytest.fixture
def base_match():
    return parse_match_report_pdf(FIXTURE_PDF, 2590834)


def test_validation_valid(base_match):
    status, warnings = MatchValidator.validate(base_match)
    assert status == "VALID"
    assert len(warnings) == 0


def test_validation_warning_on_mismatch(base_match):
    # Alter player attack points to simulate mismatch with team total
    tampered = deepcopy(base_match)
    tampered.players[0].attack_points = 99

    status, warnings = MatchValidator.validate(tampered)
    assert status == "WARNING"
    assert any("sum of player attack points" in w for w in warnings)


def test_validation_invalid_on_missing_id(base_match):
    tampered = deepcopy(base_match)
    tampered.match.match_id = 0

    status, warnings = MatchValidator.validate(tampered)
    assert status == "INVALID"
    assert any("match_id missing" in w for w in warnings)


def test_validation_invalid_on_no_players(base_match):
    tampered = deepcopy(base_match)
    tampered.players = []

    status, warnings = MatchValidator.validate(tampered)
    assert status == "INVALID"
    assert any("no players found" in w for w in warnings)
