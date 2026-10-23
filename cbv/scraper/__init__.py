"""Scraper exports are lazy: collecting source files must not open the production DB."""
from importlib import import_module

_EXPORTS = {
    'HttpClient':('client','HttpClient'),
    'fetch_game_page':('game_page','fetch_game_page'),
    'extract_match_report_url':('game_page','extract_match_report_url'),
    'download_match_report':('downloader','download_match_report'),
    'process_single_game':('downloader','process_single_game'),
    'DownloadError':('downloader','DownloadError'),
    'discover_matches':('competition','discover_matches'),
    'build_competition_url':('competition','build_competition_url'),
    'scrape_competition':('competition','scrape_competition'),
}
__all__=list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module,attribute=_EXPORTS[name]
    return getattr(import_module('cbv.scraper.'+module),attribute)
