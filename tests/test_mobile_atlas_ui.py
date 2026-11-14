"""Automated End-to-End Responsive & Interaction Suite for Atlas do Vôlei Mobile-First UI."""
import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = (BASE_DIR / "index.html").resolve()


@pytest.fixture(scope="module")
def browser_context():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    yield browser
    browser.close()
    p.stop()


def test_responsive_zero_overflow_all_breakpoints(browser_context):
    """Verifies that across 320px to 1440px there is zero global horizontal overflow."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")
    page.wait_for_selector('[data-nav="Início"]:visible')

    breakpoints = [320, 360, 375, 390, 412, 768, 1024, 1280, 1440]
    tabs = ["Início", "Jogos", "Times", "Atletas", "Análises"]

    for width in breakpoints:
        page.set_viewport_size({"width": width, "height": 844})
        for tab in tabs:
            page.locator(f'[data-nav="{tab}"]:visible').first.click()
            page.wait_for_timeout(50)

            # Assert horizontal containment
            scroll_w = page.evaluate("document.documentElement.scrollWidth")
            client_w = page.evaluate("window.innerWidth")
            assert scroll_w <= client_w, f"Horizontal overflow on tab '{tab}' at width {width}px: scrollWidth={scroll_w} > innerWidth={client_w}"

    page.close()


def test_primary_destinations_and_search(browser_context):
    """The five main destinations stay reachable alongside global search."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    # Bottom nav exposes every primary workflow, including analysis.
    nav_items = page.locator("#bottom-nav .nav-item")
    assert nav_items.count() == 5
    labels = [nav_items.nth(i).inner_text().strip().upper() for i in range(5)]
    assert labels == ["INÍCIO", "JOGOS", "TIMES", "ATLETAS", "ANÁLISES"]

    # Search bar permanently visible in header
    search_bar = page.locator("#global-search")
    assert search_bar.is_visible()
    assert search_bar.get_attribute("placeholder") is not None

    page.close()


def test_analysis_destination_opens_existing_team_analysis(browser_context):
    """Analysis is a primary destination and reuses all current team sections."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    page.locator('[data-nav="Análises"]:visible').first.click()
    assert page.locator('#main h1').inner_text().strip().casefold() == 'análises'
    assert page.locator('#analysis-team-picker').is_visible()

    analysis_nav = page.get_by_role('navigation', name='Seções de análise')
    for label in ['Rotações P1–P6', 'Ataque', 'Recepção', 'Atletas', 'Avançado', 'Comparar edições']:
        assert analysis_nav.get_by_role('button', name=label, exact=True).is_visible()
    assert analysis_nav.evaluate('element => element.scrollWidth <= element.clientWidth')

    analysis_nav.locator('[data-analysis-section="Avançado"]').click()
    assert page.get_by_role('heading', name='Análise avançada').is_visible()
    assert page.locator('[data-nav="Análises"]').first.get_attribute('aria-current') == 'page'
    page.close()


def test_analysis_season_comparison_keeps_edition_scope(browser_context):
    """Cross-season comparisons use matching competition/category/gender cohorts."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    page.locator('[data-nav="Análises"]:visible').first.click()
    page.locator('#analysis-team-picker').select_option(label='Osasco São Cristóvão Saúde')
    page.locator('[data-analysis-section="Temporadas"]').click()
    picker = page.locator('#analysis-compare-cohort')
    assert picker.is_visible()
    assert picker.locator('option').count() == 2
    picker.select_option(label='2025–26')

    headers = page.locator('.season-comparison-table thead th')
    assert headers.count() == 4
    assert 'recorte selecionado' in headers.nth(1).inner_text().casefold()
    assert 'edição comparada' in headers.nth(2).inner_text().casefold()
    assert '2025–26' in headers.nth(2).inner_text()
    assert page.locator('.season-comparison-table tbody tr').count() == 6
    assert 'n=' in page.locator('.season-comparison-table tbody tr').first.inner_text()
    assert 'diferença' in page.locator('.season-comparison-note').inner_text().casefold()
    assert page.get_by_role('region', name='Tabela de comparação por temporada; percorra horizontalmente para ver todas as colunas').is_visible()
    page.locator('[data-analysis-metric="so"]').click()
    assert page.locator('#app-sheet.open').is_visible()
    assert 'fórmula' in page.locator('#sheet-body').inner_text().casefold()
    page.locator('#sheet-close').click()
    page.close()


def test_sync_health_bottom_sheet(browser_context):
    """Verifies sync status chip and bottom sheet showing source health."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    badge = page.locator("#sync-status-badge")
    assert badge.is_visible()

    # Click opens bottom sheet
    badge.click()
    page.wait_for_selector("#app-sheet.open")
    title = page.locator("#sheet-title").inner_text().strip().upper()
    assert "SAÚDE DAS FONTES" in title
    assert page.locator("#sheet-handle").is_visible()

    # Close via button
    page.locator("#sheet-close").click()
    page.wait_for_timeout(150)
    assert not page.locator("#app-sheet").evaluate("el => el.classList.contains('open')")

    page.close()


def test_team_profile_rotations_follow_setter_position(browser_context):
    """The selected rotation determines the setter zone and front/back row."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    # Navigate to Times
    page.locator('[data-nav="Times"]:visible').first.click()
    page.wait_for_selector(".team-hero-card")

    # Click the Rotações section tab
    page.locator('.section-tab-btn:has-text("Rotações")').click()
    page.wait_for_selector(".rotation-widget-box")

    # Check P1-P6 buttons
    p_buttons = page.locator(".p-selector .p-btn")
    assert p_buttons.count() == 6

    # Click P4
    p4 = page.locator('.p-selector .p-btn:has-text("P4")')
    p4.click()
    page.wait_for_timeout(50)
    assert p4.evaluate("el => el.classList.contains('active')")

    assert 'Levantadora na zona 4' in page.locator('.court-svg').text_content()
    assert 'rede' in page.locator('.court-svg').text_content()
    assert page.locator('#setter-fundo, #setter-rede').count() == 0
    page.locator('.p-selector .p-btn:has-text("P1")').click()
    assert 'Levantadora na zona 1' in page.locator('.court-svg').text_content()
    assert 'fundo' in page.locator('.court-svg').text_content()

    page.close()


def test_athlete_profile_and_metric_explainer_sheet(browser_context):
    """Verifies athlete metrics carousel and canonical bottom sheet explainer."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    # Navigate to Atletas
    page.locator('[data-nav="Atletas"]:visible').first.click()
    page.wait_for_selector(".athlete-profile-card")

    # Big stats and metric carousel visible
    assert page.locator(".athlete-big-stats").is_visible()
    metric_cards = page.locator(".metric-card-interactive")
    assert metric_cards.count() >= 3

    # Click a metric card to open explanation
    metric_cards.first.click()
    page.wait_for_selector("#app-sheet.open")
    title = page.locator("#sheet-title").inner_text().strip().upper()
    assert "DEFINIÇÃO ESTATÍSTICA" in title

    sheet_text = page.locator("#sheet-body").inner_text()
    assert any(tag in sheet_text for tag in ["OBSERVADO", "RECONSTRUÍDO", "DERIVADO", "MODELADO", "EXPERIMENTAL"])
    assert "Fórmula" in sheet_text or "Amostra" in sheet_text

    page.locator("#sheet-close").click()
    page.close()


def test_compare_dock_drag_and_tap(browser_context):
    """Verifies + Comparar buttons populate floating dock and trigger comparison."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    # Home has athlete / team cards with + Comparar
    compare_btns = page.locator("[data-add-compare-athlete], [data-add-compare-team]")
    assert compare_btns.count() >= 2

    dock = page.locator("#compare-dock")
    assert dock.is_hidden()

    # Add first item
    compare_btns.nth(0).click()
    assert dock.is_visible()
    assert "(1/2)" in page.locator("#dock-count").inner_text()
    assert page.locator("#btn-compare-action").is_disabled()

    # Add second item
    compare_btns.nth(1).click()
    assert "(2/2)" in page.locator("#dock-count").inner_text()
    assert not page.locator("#btn-compare-action").is_disabled()

    # Clear
    page.locator("#btn-compare-clear").click()
    assert dock.is_hidden()

    page.close()


def test_global_live_search(browser_context):
    """Verifies search input filters teams and athletes in real time."""
    page = browser_context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(INDEX_HTML.as_uri(), wait_until="domcontentloaded")

    search_input = page.locator("#global-search")
    dropdown = page.locator("#global-search-results")
    assert dropdown.is_hidden()

    search_input.fill("Minas")
    page.wait_for_timeout(200)
    assert dropdown.is_visible()
    assert dropdown.locator(".search-item").count() > 0

    page.close()
