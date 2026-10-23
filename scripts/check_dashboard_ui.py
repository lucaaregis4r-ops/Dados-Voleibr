"""Optional browser QA: pip install playwright; requires local Google Chrome."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
output=root/'temp_inspect'/'ui'
output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('https://fonts.googleapis.com/**',lambda route:route.abort())
    page.route('https://fonts.gstatic.com/**',lambda route:route.abort())
    page.goto((root/'index.html').as_uri(),wait_until='domcontentloaded')
    page.wait_for_selector('.kpis')
    for width in [1440,1024,768,390]:
        page.set_viewport_size({'width':width,'height':1000})
        page.screenshot(path=str(output/f'voleibr-{width}.png'),full_page=True,timeout=20000,animations='disabled')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Overflow {width}'
        assert page.locator('.kpi').count()==5
    page.set_viewport_size({'width':1440,'height':1000})
    for i in range(page.locator('#competition option').count()):
        value=page.locator('#competition option').nth(i).get_attribute('value')
        page.select_option('#competition',value)
        assert page.locator('.kpis').count()==1
    for primary in ['Equipes','Confronto','Partidas','Dados']:
        page.get_by_role('button',name=primary,exact=True).click()
        for sub in page.locator('.subnav button').all_text_contents():
            page.locator('.subnav').get_by_role('button',name=sub,exact=True).click()
            assert page.locator('main h2,main h3,main .empty,main table').count()>0, (primary,sub)
            page.set_viewport_size({'width':390,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Overflow {primary}/{sub}'
            page.set_viewport_size({'width':1440,'height':1000})
    # Exercise a fitted model rather than only CBS's small sample.
    page.select_option('#competition','SUPERLIGA · A')
    page.get_by_role('button',name='Confronto',exact=True).click()
    page.locator('.subnav').get_by_role('button',name='Modelo',exact=True).click()
    pair=page.evaluate('C().model_matchups[0]')
    page.select_option('#team',pair['team_a'])
    page.select_option('#opponent',pair['team_b'])
    assert page.locator('.prob').count()==1
    page.screenshot(path=str(output/'voleibr-modelo.png'),full_page=True,timeout=20000,animations='disabled')
    page.get_by_role('button',name='Visão geral',exact=True).click()
    page.locator('svg [data-team]').first.press('Enter')
    assert page.get_by_role('button',name='Equipes',exact=True).get_attribute('aria-current')=='page'
    assert not errors, errors
    print(json.dumps({'widths':[1440,1024,768,390],'tested':'all destinations and subpages, cohort filters, model, keyboard scatter','errors':errors},ensure_ascii=False))
    browser.close()
