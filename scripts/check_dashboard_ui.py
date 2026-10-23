"""Visual and interaction checks. Optional: pip install playwright; python -m playwright install chromium."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'temp_inspect' / 'ui'
OUTPUT.mkdir(parents=True, exist_ok=True)
WIDTHS = (1440, 1024, 768, 390)


def navigate(page, title):
    button = page.locator('#primary').get_by_role('button', name=title, exact=True)
    if not button.is_visible():
        page.locator('#menu-toggle').click()
    button.click()


def check_page(page, name, width):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, width, 'page overflow')
    assert page.locator('main h1').count() == 1, (name, width, 'one page title')
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(OUTPUT / f'{name}-{width}.png'), full_page=True, animations='disabled', timeout=20000)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True,
        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    # The exported page must work with no external fonts, scripts or data requests.
    page.route('https://**/*', lambda route: route.abort())
    page.goto((ROOT / 'index.html').as_uri(), wait_until='domcontentloaded')
    page.wait_for_selector('.kpis')
    for width in WIDTHS:
        page.set_viewport_size({'width': width, 'height': 1000})
        navigate(page, 'Visão geral')
        assert page.locator('.kpi').count() == 3
        assert page.locator('.rank-list li').count() == 10
        assert not page.get_by_text('Ver projeção', exact=True).count()
        if width > 900:
            assert page.locator('#sidebar').bounding_box()['width'] == 232
        else:
            assert page.locator('#menu-toggle').is_visible()
        if width == 390:
            assert page.locator('svg.scatter').bounding_box()['height'] >= 360
        check_page(page, 'overview', width)

        # Select an actual team through the global search, using keyboard navigation.
        chosen = page.evaluate('C().teams.find(t=>t.metrics.so.n>100 && t.athletes.length).team')
        page.locator('#team-search').fill(chosen)
        page.locator('#team-search').press('ArrowDown')
        page.locator('#team-results button').first.press('Enter')
        assert page.locator('#primary [aria-current="page"]').inner_text() == 'Equipes'
        assert page.locator('.kpi').count() == 4
        assert page.locator('.rotation').count() == 6
        assert page.locator('#athlete-table th').count() == 9
        page.locator('[data-athlete-sort="attacks"]').click()
        attempts = [int(value.replace('.', '')) for value in page.locator('#athlete-table tbody tr td:nth-child(4)').all_text_contents()]
        assert attempts == sorted(attempts, reverse=True)
        page.locator('[data-athlete-sort="attacks"]').click()
        attempts = [int(value.replace('.', '')) for value in page.locator('#athlete-table tbody tr td:nth-child(4)').all_text_contents()]
        assert attempts == sorted(attempts)
        first_name = page.locator('#athlete-table tbody tr td').first.inner_text()
        page.locator('#athlete-search').fill(first_name)
        assert page.locator('#athlete-table tbody tr').count() >= 1
        assert all(first_name.casefold() in name.casefold() for name in page.locator('#athlete-table tbody tr td:first-child').all_text_contents())
        page.locator('#athlete-search').fill('')
        check_page(page, 'team', width)

        navigate(page, 'Confrontos')
        pair = page.evaluate('C().model_matchups[0]')
        page.select_option('#team', pair['team_a'])
        page.select_option('#opponent', pair['team_b'])
        assert not page.locator('#projection').evaluate('(element)=>element.open')
        assert page.locator('main > section').count() == 3
        check_page(page, 'matchup', width)
        page.locator('#projection > summary').click()
        assert page.locator('.prob-row').count() == 2
        check_page(page, 'projection', width)

        navigate(page, 'Partidas')
        page.get_by_role('button', name='Encerradas', exact=True).click()
        assert page.locator('main table th').count() == 6
        check_page(page, 'matches', width)
        page.locator('[data-match]').first.click()
        assert page.get_by_role('heading', name='Comparação geral', exact=True).count() == 1
        assert not page.locator('#projection').count()
        assert page.get_by_role('heading', name='Sets', exact=True).count() == 1
        check_page(page, 'match', width)
        page.locator('[data-back-matches]').click()
        page.get_by_role('button', name='Súmulas', exact=True).click()
        assert page.locator('[data-match]').count() > 0
        page.get_by_role('button', name='Próximas', exact=True).click()
        check_page(page, 'upcoming', width)

        navigate(page, 'Dados')
        for title in ('Cobertura', 'Métricas', 'Atualização'):
            assert page.get_by_role('heading', name=title, exact=True).count() == 1
        assert page.get_by_text('Experimental', exact=True).count() == 1
        check_page(page, 'data', width)
        assert not errors, errors

    # Scope filters must select a complete, existing competition/gender/season cohort.
    navigate(page, 'Visão geral')
    for competition in page.locator('#competition option').all_text_contents():
        page.select_option('#competition', label=competition)
        for gender in page.locator('#gender option').all_text_contents():
            page.select_option('#gender', label=gender)
            for season in page.locator('#season option').all_text_contents():
                page.select_option('#season', label=season)
                assert page.locator('.kpi').count() == 3
                assert page.evaluate('C().gender') == gender
                assert page.evaluate('C().season') == season
    # The scatter point is an accessible route to the selected team.
    page.locator('svg [data-team]').first.press('Enter')
    assert page.locator('#primary [aria-current="page"]').inner_text() == 'Equipes'
    assert not errors, errors
    print(json.dumps({'widths': WIDTHS, 'pages': ['overview', 'team', 'matchup', 'match', 'matches', 'upcoming', 'data'],
        'checks': ['overflow', 'navigation', 'search', 'sorting', 'collapsed projection', 'cohort filters', 'keyboard', 'offline fonts'], 'errors': errors}))
    browser.close()
