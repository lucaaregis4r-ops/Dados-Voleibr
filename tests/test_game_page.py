"""Unit tests for CBV game page fetching and link extraction."""

from pathlib import Path
import pytest

from cbv.scraper.game_page import extract_game_links, extract_match_report_url
from cbv.scraper.downloader import validate_pdf_bytes

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "game_page_2590834.html"


def test_extract_match_report_url_from_fixture():
    """Validates that extract_match_report_url properly finds the PDF link in real fixture HTML."""
    assert FIXTURE_PATH.exists(), "Fixture game_page_2590834.html must exist"
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    report_url = extract_match_report_url(html)
    assert report_url is not None
    assert report_url.endswith(".pdf")
    assert "2026-10-16-RJ-MG.pdf" in report_url
    assert "fra1.digitaloceanspaces.com/pls-api/matches/2590834" in report_url


def test_extract_game_links():
    """Checks that both Scoresheet and Match Report URLs are discovered if available."""
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    links = extract_game_links(html)

    assert "match_report_url" in links
    assert "scoresheet_url" in links
    assert links["match_report_url"] is not None
    assert "2026-10-16-RJ-MG.pdf" in links["match_report_url"]
    assert links["scoresheet_url"] is not None
    assert "RJ-MG-scoresheet.pdf" in links["scoresheet_url"]


def test_extract_match_report_url_missing():
    """Returns None when no match report link exists in HTML."""
    dummy_html = "<html><body><a href='/other'>Outro link</a></body></html>"
    assert extract_match_report_url(dummy_html) is None


def test_validate_pdf_bytes():
    """Tests the PDF validation function for proper header check."""
    assert validate_pdf_bytes(b"%PDF-1.4\n...") is True
    assert validate_pdf_bytes(b"   %PDF-1.7\n...") is True
    assert validate_pdf_bytes(b"<html><body>Erro 404</body></html>") is False
    assert validate_pdf_bytes(b"") is False
    assert validate_pdf_bytes(None) is False
