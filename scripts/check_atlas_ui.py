"""Offline static Atlas interaction and responsive checks. Run after export."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'temp_inspect/atlas-ui';OUT.mkdir(parents=True,exist_ok=True)

def navigate(page,name):
    button=page.locator('#primary').get_by_role('button',name=name,exact=True)
    if not button.is_visible():page.locator('#menu-toggle').click()
    button.click()


def check(page,name,width):
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(name,width,'overflow')
    assert 'NaN' not in page.locator('main').inner_text(),(name,width,'NaN')
    page.screenshot(path=str(OUT/f'{name}-{width}.png'),full_page=True,animations='disabled',timeout=30000)


with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('https://**/*',lambda route:route.abort())
    page.goto(Path(os.getenv('CBV_UI_HTML',ROOT/'index.html')).resolve().as_uri(),wait_until='domcontentloaded',timeout=60000)
    page.wait_for_selector('.kpis')
    for width in [1440,1024,768,390]:
        page.set_viewport_size(dict(width=width,height=1000))
        navigate(page,'Visão geral');check(page,'overview',width)
        # Pick a covered cohort/team where possible; never assume fabricated coverage.
        choice=page.evaluate("""(()=>{for(let i=0;i<DATA.cohorts.length;i++){const c=DATA.cohorts[i],t=Object.values(c.atlas_teams||{}).find(t=>t.coverage.rotation_rallies);if(t)return {cohort:i,team:t.team}}return {cohort:0,team:DATA.cohorts[0].teams[0].team}})()""")
        page.evaluate('(s)=>{Object.assign(state,s,{page:"Equipes"});render()}',choice)
        check(page,'team',width)
        if page.locator('[data-layer]').count():
            page.locator('[data-layer="bp"]').click();assert page.locator('[data-layer="bp"]').get_attribute('class')=='active'
            page.locator('[data-cell]').first.click();assert page.locator('.matrix-detail').count()==1
            page.locator('[data-rotation="4"]').first.click();assert 'P4' in page.locator('.rotation-detail h3').inner_text()
        page.evaluate('()=>{state.opponent=C().teams.find(t=>t.team!==state.team)?.team;state.page="Confrontos";render()}')
        check(page,'matchup',width)
        selected=page.evaluate('()=>{const mid=Object.keys(C().rallies||{})[0];state.matchId=mid||C().matches[0].match_id;state.rallyIndex=0;state.page="Partidas";render();return Boolean(mid)}')
        check(page,'match',width)
        if selected:
            before=page.locator('.scoreboard strong').inner_text();page.locator('[data-step="1"]').click()
            assert page.locator('.scoreboard strong').inner_text()!=before
            assert page.locator('#rally-slider').input_value()=='1'
        navigate(page,'Atletas');check(page,'athletes',width)
        page.locator('#athlete-search').fill('zzzz-no-athlete');assert page.locator('#athlete-table tbody').inner_text()=='Nenhum atleta encontrado.'
        page.locator('#athlete-search').fill('')
        if page.locator('[data-athlete]').count():
            page.locator('[data-athlete]').first.click();assert page.locator('.athlete-profile').count()==1
        navigate(page,'Dados');check(page,'data',width)
        assert page.get_by_text('Abrir caderno metodológico',exact=True).count()
    assert not errors,errors
    assert page.evaluate('document.fonts.check("400 12px Inter")')
    browser.close()
print('Atlas: 6 páginas × 4 larguras; quadra, matriz, replay, busca e fontes offline verificados.')
