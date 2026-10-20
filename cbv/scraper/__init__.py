"""Scraper module for CBV web pages and match reports."""

from cbv.scraper.client import HttpClient
from cbv.scraper.game_page import fetch_game_page, extract_match_report_url
from cbv.scraper.downloader import download_match_report, process_single_game, DownloadError
from cbv.scraper.competition import (
    discover_matches,
    build_competition_url,
    scrape_competition,
)

__all__ = [
    "HttpClient",
    "fetch_game_page",
    "extract_match_report_url",
    "download_match_report",
    "process_single_game",
    "DownloadError",
    "discover_matches",
    "build_competition_url",
    "scrape_competition",
]

