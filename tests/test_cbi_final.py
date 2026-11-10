from cbv.scraper.cbi import finished_match_ids, final_url


def test_only_finished_match_links_are_imported():
    html = '''<article><span>Encerrado</span><a href="/jogo/2601633">Veja como foi</a></article>
    <article><span>Ao vivo</span><a href="/jogo/2601634">Acompanhe</a></article>
    <article><span>10/11 às 13:00</span><a href="/jogo/2601635">Detalhes</a></article>
    <article><span>Encerrado</span><a href="/jogo/2601633">Veja como foi</a></article>'''
    assert finished_match_ids(html) == [2601633]


def test_final_urls_identify_gender_and_season():
    assert final_url('feminino', 2026) == 'https://cbv.com.br/volei-de-quadra/cbi/2026/sub-16/feminino/fase-final'
    assert final_url('masculino', 2026).endswith('/2026/sub-16/masculino/fase-final')
