from pathlib import Path
from cbv.storage.raw import RawStore,digest
from cbv.scraper.sources import discover_source_links,SourceCollector


def test_sources_share_match_identifier():
    html=Path('tests/fixtures/game_page_2590834.html').read_text()
    links=discover_source_links(html,2590834)
    assert {'scoresheet','match_report','play_by_play','libero_report'}<=links.keys()
    assert '2590834' in links['scoresheet']
    assert not discover_source_links(html,1)


def test_raw_hash_idempotency_and_corruption(tmp_path):
    store=RawStore(tmp_path,42)
    path=store.put('scoresheet',b'%PDF-original','https://cbv.test/42','scoresheet.pdf','application/pdf','2026-01-01T00:00:00+00:00')
    before=path.stat().st_mtime_ns
    store.put('scoresheet',b'%PDF-original','https://cbv.test/42','scoresheet.pdf','application/pdf',None,legacy=True)
    assert path.stat().st_mtime_ns==before
    assert store.cached('scoresheet')==path
    path.write_bytes(b'corrupt')
    assert store.cached('scoresheet') is None
    assert store.manifest['sources']['scoresheet']['status']=='CORRUPT'


def test_failed_refresh_keeps_snapshot(tmp_path):
    store=RawStore(tmp_path,1)
    store.put('match_report',b'%PDF-valid','url','match_report.pdf','application/pdf')
    store.failure('match_report','url','FAILED','network')
    assert store.cached('match_report')
    assert store.manifest['sources']['match_report']['last_failed_attempt']['error']=='network'


def test_missing_scoresheet_does_not_block_report(tmp_path):
    legacy=tmp_path/'legacy';(legacy/'pages').mkdir(parents=True);(legacy/'reports').mkdir()
    url='https://fra1.digitaloceanspaces.com/pls-api/matches/42-token/report.pdf'
    (legacy/'pages/42.html').write_text(f'<a href="{url}">Match Report</a>')
    (legacy/'reports/42.pdf').write_bytes(b'%PDF-old-valid')
    collector=SourceCollector(tmp_path/'matches',legacy)
    collector._get=lambda url: (_ for _ in ()).throw(AssertionError('No request expected'))
    manifest=collector.collect(42)
    assert manifest['sources']['match_report']['status']=='AVAILABLE'
    assert manifest['sources']['scoresheet']['status']=='UNAVAILABLE'
    assert manifest['sources']['match_report']['fetched_at'] is None
