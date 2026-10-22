"""Unit tests for competition URL parsing and scraping."""

import pytest
from cbv.scraper.competition import parse_competition_url


def test_parse_competition_url_standard():
    url = "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-especial"
    meta = parse_competition_url(url)
    assert meta["competition"] == "cbs"
    assert meta["season"] == 2026
    assert meta["gender"] == "feminino"
    assert meta["category"] == "sub18"
    assert meta["division"] == "especial"
    assert meta["url"] == url


def test_parse_competition_url_sub16_with_query_params():
    url = "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-16-especial?tab=jogos&fase=classificatoria"
    meta = parse_competition_url(url)
    assert meta["competition"] == "cbs"
    assert meta["season"] == 2026
    assert meta["gender"] == "feminino"
    assert meta["category"] == "sub16"
    assert meta["division"] == "especial"
    assert meta["url"] == "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-16-especial"


def test_parse_competition_url_missing_protocol_and_trailing_slash():
    url = "cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-primeira-divisao/"
    meta = parse_competition_url(url)
    assert meta["competition"] == "cbs"
    assert meta["season"] == 2026
    assert meta["gender"] == "feminino"
    assert meta["category"] == "sub18"
    assert meta["division"] == "primeira-divisao"
    assert meta["url"] == "https://cbv.com.br/volei-de-quadra/cbs/2026/feminino/sub-18-primeira-divisao"


def test_parse_competition_url_custom_fallback():
    url = "https://cbv.com.br/competicao/cbs-feminino-novembro-2026"
    meta = parse_competition_url(url)
    assert meta["gender"] == "feminino"
    assert meta["season"] == 2026
    assert "https://cbv.com.br/competicao/cbs-feminino-novembro-2026" in meta["url"]
