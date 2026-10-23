"""Unit tests for DuckDB repository."""

from pathlib import Path
import pytest
from cbv.database.repository import DatabaseRepository
from cbv.parser.match_report import parse_match_report_pdf
from tests.test_match_report import FIXTURE_PDF


@pytest.fixture
def test_repo(tmp_path):
    db_file = tmp_path / "test_cbv.duckdb"
    return DatabaseRepository(db_path=db_file)


@pytest.fixture
def sample_match_data():
    return parse_match_report_pdf(FIXTURE_PDF, 2590834)


def test_db_init(test_repo):
    with test_repo.get_connection() as conn:
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        assert "matches" in table_names
        assert "sets" in table_names
        assert "player_match_stats" in table_names
        assert "team_match_stats" in table_names


def test_save_and_query_match_data(test_repo, sample_match_data):
    assert test_repo.match_exists(2590834) is False
    test_repo.save_match_data(sample_match_data)
    assert test_repo.match_exists(2590834) is True

    with test_repo.get_connection() as conn:
        # Check match
        m = conn.execute("SELECT home_team, away_team, home_sets, away_sets, validation_status FROM matches WHERE match_id = 2590834").fetchone()
        assert m == ("RIO DE JANEIRO", "MINAS GERAIS", 1, 2, "VALID")

        # Check sets count
        sets_count = conn.execute("SELECT count(*) FROM sets WHERE match_id = 2590834").fetchone()[0]
        assert sets_count == 3

        # Check players count
        players_count = conn.execute("SELECT count(*) FROM player_match_stats WHERE match_id = 2590834").fetchone()[0]
        assert players_count == 20

        # Check teams count
        teams_count = conn.execute("SELECT count(*) FROM team_match_stats WHERE match_id = 2590834").fetchone()[0]
        assert teams_count == 2


def test_idempotent_save(test_repo, sample_match_data):
    # Save first time
    test_repo.save_match_data(sample_match_data)
    # Save second time
    test_repo.save_match_data(sample_match_data)

    with test_repo.get_connection() as conn:
        players_count = conn.execute("SELECT count(*) FROM player_match_stats WHERE match_id = 2590834").fetchone()[0]
        assert players_count == 20


def test_ingestion_invalidates_cached_missing_team(test_repo, sample_match_data, monkeypatch):
    """A team first looked up before collection must appear without restarting the app."""
    import cbv.analysis.tactics as tactics
    from cbv.analysis.setter_distribution import infer_team_tactical_roles
    monkeypatch.setattr(tactics, 'default_repo', test_repo)
    tactics.get_team_tactical_dossier.cache_clear()
    infer_team_tactical_roles.cache_clear()
    try:
        assert tactics.get_team_tactical_dossier('MINAS GERAIS', season=None) is None
        assert infer_team_tactical_roles('MINAS GERAIS', season=None) is None
        test_repo.save_match_data(sample_match_data)
        dossier = tactics.get_team_tactical_dossier('MINAS GERAIS', season=None)
        assert dossier is not None
        assert dossier['record']['games'] == 1
        assert infer_team_tactical_roles('MINAS GERAIS', season=None) is not None
    finally:
        tactics.get_team_tactical_dossier.cache_clear()
        infer_team_tactical_roles.cache_clear()


def test_invalid_refresh_cannot_replace_last_valid_report(test_repo,sample_match_data):
    test_repo.save_match_data(sample_match_data)
    bad=sample_match_data.model_copy(deep=True);bad.validation_status='FAILED';bad.match.home_sets=0
    test_repo.save_match_data(bad)
    with test_repo.get_connection() as conn:
        assert conn.execute('SELECT home_sets,validation_status FROM matches WHERE match_id=2590834').fetchone()==(1,'VALID')
        assert conn.execute('SELECT status FROM match_ingest_attempts WHERE match_id=2590834').fetchone()[0]=='FAILED'
        assert conn.execute('SELECT count(*) FROM player_match_stats WHERE match_id=2590834').fetchone()[0]==20
