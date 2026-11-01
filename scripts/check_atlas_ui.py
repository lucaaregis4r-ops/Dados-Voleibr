"""Smoke-test the published static Atlas at desktop and mobile widths."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = Path(os.getenv('CBV_UI_HTML', ROOT / 'index.html')).resolve().as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(HTML, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('#main')
    for width in (1440, 1024, 768, 390):
        page.set_viewport_size({'width': width, 'height': 1000})
        for label in ('Início', 'Jogos', 'Times', 'Atletas'):
            page.locator(f'[data-nav="{label}"]:visible').first.click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (label, width, 'overflow')
            assert 'NaN' not in page.locator('#main').inner_text(), (label, width, 'NaN')
        page.locator('[data-nav="Jogos"]:visible').first.click()
        match = page.locator('#main [data-match]').first
        if match.count():
            match.click()
            assert page.get_by_role('button', name='← Voltar para Jogos').is_visible()
        page.locator('[data-nav="Times"]:visible').first.click()
        page.get_by_role('button', name='Rotações', exact=True).click()
        page.get_by_role('button', name='P4', exact=True).first.click()
        assert 'Levantadora na zona 4' in page.locator('.court-svg').text_content()
        page.get_by_role('button', name='P1', exact=True).first.click()
        assert 'Levantadora na zona 1' in page.locator('.court-svg').text_content()
    assert not errors, errors
    browser.close()
print('Atlas: navegação, partidas, rotações e responsividade verificadas.')
