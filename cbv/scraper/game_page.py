"""Game page fetcher and parser for extracting match report URLs."""

from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from cbv.config import (
    BASE_URL,
    RAW_PAGES_DIR,
    logger,
)
from cbv.scraper.client import HttpClient, default_client


def get_game_page_cache_path(game_id: int) -> Path:
    """Returns the local path where raw HTML is stored."""
    return RAW_PAGES_DIR / f"{game_id}.html"


def fetch_game_page(
    game_id: int,
    force: bool = False,
    client: Optional[HttpClient] = None,
) -> tuple[str, bool]:
    """
    Fetches the HTML page for a game_id, utilizing local cache unless force=True.
    Returns a tuple (html_content, was_cached).
    """
    cache_path = get_game_page_cache_path(game_id)

    if not force and cache_path.exists():
        logger.info(f"game={game_id} page loaded from cache")
        return cache_path.read_text(encoding="utf-8"), True

    client = client or default_client
    url = f"{BASE_URL}/jogo/{game_id}"
    logger.info(f"game={game_id} fetching page from {url}")

    response = client.get(url)
    html = response.text

    cache_path.write_text(html, encoding="utf-8")
    logger.info(f"game={game_id} page downloaded")
    return html, False


def extract_game_links(html: str, base_url: str = BASE_URL) -> Dict[str, Optional[str]]:
    """
    Extracts relevant document links from game HTML, such as Match Report and Scoresheet.
    """
    soup = BeautifulSoup(html, "lxml")
    links: Dict[str, Optional[str]] = {
        "match_report_url": None,
        "scoresheet_url": None,
    }

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(separator=" ", strip=True).lower()
        title = (a.get("title") or "").lower()
        aria_label = (a.get("aria-label") or "").lower()
        combined_text = f"{text} {title} {aria_label} {href.lower()}"

        # Check for Match Report
        if "match report" in combined_text or "relatório" in combined_text or "relatorio" in combined_text:
            if not links["match_report_url"]:
                links["match_report_url"] = urljoin(base_url, href)

        # Check for Scoresheet
        if "scoresheet" in combined_text or "súmula" in combined_text or "sumula" in combined_text:
            if not links["scoresheet_url"]:
                links["scoresheet_url"] = urljoin(base_url, href)

    return links


def extract_match_report_url(html: str, base_url: str = BASE_URL) -> Optional[str]:
    """
    Finds the Match Report URL from game page HTML.
    Looks for links whose text, title or context contains 'Match Report'.
    """
    links = extract_game_links(html, base_url)
    return links.get("match_report_url")
