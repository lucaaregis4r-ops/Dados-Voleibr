"""Exercise the current templates against real exported data at phone width."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from functools import partial
import pytest

ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture(scope='module')
def atlas_server(tmp_path_factory):
    root = tmp_path_factory.mktemp('atlas-phone')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    marker = '// Atlas do Vôlei — Mobile-First Statistical Atlas & Scouting Engine'
    start = html.index(marker)
    end = html.index('\nrender();\n</script>', start)
    html = html[:start] + (ROOT / 'cbv/export/templates/atlas.js').read_text(encoding='utf-8') + html[end:]
    html = html.replace('</head>', '<style>' + (ROOT / 'cbv/export/templates/atlas.css').read_text(encoding='utf-8') + '</style></head>', 1)
    (root / 'index.html').write_text(html, encoding='utf-8')
    (root / 'exports').symlink_to(ROOT / 'exports', target_is_directory=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/'
    server.shutdown()
    thread.join()

@pytest.fixture
def phone(atlas_server):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(atlas_server, wait_until='domcontentloaded')
        yield page, errors
        browser.close()

def test_team_tabs_advanced_and_roster_navigation(phone):
    page, errors = phone
    page.locator('[data-nav="Times"]:visible').first.click()
    assert page.locator('#team-picker').is_visible()
    for label in ['Visão geral', 'Rotações', 'Ataque', 'Passe', 'Atletas', 'Avançado']:
        assert page.get_by_role('button', name=label, exact=True).is_visible()
    page.get_by_role('button', name='Avançado', exact=True).click()
    assert page.get_by_role('heading', name='Análise avançada').is_visible()
    page.get_by_role('button', name='Ver análise de presença').click()
    page.wait_for_function("!document.querySelector('#tactical-lineups-container').textContent.includes('Carregando')")
    page.get_by_role('button', name='Atletas', exact=True).last.click()
    button = page.locator('[data-open-athlete]').first
    name = button.get_attribute('data-open-athlete')
    button.click()
    assert page.locator('#athlete-profile h2').inner_text().casefold() == name.casefold()
    assert not errors

def test_pick_another_athlete_and_search_full_roster(phone):
    page, errors = phone
    page.locator('[data-nav="Atletas"]:visible').first.click()
    page.wait_for_function("athleteLoadState.get(C().id) === 'loaded'", timeout=30000)
    choices = page.locator('#main [data-open-athlete]')
    assert choices.count() > 5
    button = choices.nth(1)
    name = button.get_attribute('data-open-athlete')
    button.click()
    assert page.locator('#athlete-profile h2').inner_text().casefold() == name.casefold()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
