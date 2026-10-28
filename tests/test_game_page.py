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


def test_fetch_sumulas_modern_li_layout(monkeypatch):
    """Verifies that fetch_sumulas_table handles the modern Tailwind <li> component layout."""
    from cbv.scraper.superliga import fetch_sumulas_table
    import io

    sample_html = """
    <ul>
      <li class="grid">
        <div><p class="text-xs">27/10/2026 · 21h00</p></div>
        <div>
          <span class="truncate"><span class="hidden sm:inline">PRAIA CLUBE UBERLANDIA VOLEI</span></span>
          <span class="tabular-nums font-bold">3 × 0</span>
          <span class="truncate"><span class="hidden sm:inline">VIAPOL VÔLEI SÃO JOSÉ</span></span>
        </div>
        <div>
          <a href="https://fra1.digitaloceanspaces.com/pls-api/matches/2584866-abc/PCU-VSJ-scoresheet.pdf">Súmula</a>
        </div>
      </li>
    </ul>
    """
    class DummyResp:
        def read(self):
            return sample_html.encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=20: DummyResp())
    matches = fetch_sumulas_table("https://cbv.com.br/dummy")
    assert len(matches) == 1
    m = matches[0]
    assert m["match_id"] == 2584866
    assert m["home_team"] == "PRAIA CLUBE UBERLANDIA VOLEI"
    assert m["away_team"] == "VIAPOL VÔLEI SÃO JOSÉ"
    assert m["home_sets"] == 3
    assert m["away_sets"] == 0
    assert m["scoresheet_url"] is not None
