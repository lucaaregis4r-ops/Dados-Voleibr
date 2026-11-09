const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('opening a match preserves its selection; regular navigation clears it', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const router = source.slice(source.indexOf('function navigateTo('), source.indexOf('// METRIC BOTTOM SHEET'));
  const context = { state: {page: 'Início', matchId: null}, document: {querySelectorAll: () => []}, window: {scrollTo() {}}, render() {} };
  vm.createContext(context);
  vm.runInContext(router, context);
  context.navigateTo('Jogos', '2585002');
  assert.equal(context.state.matchId, '2585002');
  context.navigateTo('Times');
  assert.equal(context.state.matchId, null);
});

test('health is stale after 36h and unknown when critical sources are pending', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const code = source.slice(source.indexOf('function effectiveSyncStatus('), source.indexOf('// SYNC HEALTH BOTTOM SHEET'));
  const context = {}; vm.createContext(context); vm.runInContext(code, context);
  const now = Date.parse('2026-11-01T12:00:00Z');
  assert.equal(context.effectiveSyncStatus({status:'HEALTHY', finished_at:'2026-10-29T12:00:00Z'}, now), 'STALE');
  assert.equal(context.effectiveSyncStatus({status:'HEALTHY', finished_at:'2026-11-01T11:00:00Z', sources:{report:{severity:'CRITICAL',status:'PENDING'}}}, now), 'UNKNOWN');
  assert.equal(context.effectiveSyncStatus({status:'HEALTHY', finished_at:'2026-11-01T11:00:00Z', sources:{report:{severity:'CRITICAL',status:'HEALTHY',attempted:599,successful:0}}}, now), 'UNKNOWN');
  assert.equal(context.effectiveSyncStatus({status:'HEALTHY', finished_at:'2026-11-01T11:00:00Z', sources:{report:{severity:'CRITICAL',status:'HEALTHY',attempted:1,successful:1}}}, now), 'HEALTHY');
});

test('health sheet labels unavailable play-by-play and leaves unknown counts blank', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const code = source.slice(source.indexOf('function effectiveSyncStatus('), source.indexOf('function availableFilterChoices('));
  let sheet;
  const context = {
    DATA: {sync_health: {sources: {play_by_play: {status: 'HEALTHY', attempted: 613, successful: 0}}}},
    BottomSheet: {open(data) { sheet = data; }},
    esc: value => value, dateText: () => '—', num: value => String(value ?? '—')
  };
  vm.createContext(context);
  vm.runInContext(code, context);
  context.openSyncHealthSheet();
  assert.match(sheet.contentHtml, /Indisponível/);
  assert.doesNotMatch(sheet.contentHtml, /583|68543|19669/);
  context.DATA.sync_health.validation = {rallies: 0};
  context.openSyncHealthSheet();
  assert.match(sheet.contentHtml, /Rallies<\/span>\s*<span class="val">0/);
});

test('upcoming games exclude past and completed matches and show the nearest first in Brasília time', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const code = source.slice(source.indexOf('// 5. SCREEN 1'), source.indexOf('function renderHomeFeed('));
  const context = {};
  vm.createContext(context);
  vm.runInContext(code, context);
  const upcoming = [
    {match_id: 1, match_date: '2026-11-08'},
    {match_id: 2, match_date: '2026-11-10'},
    {match_id: 3, match_date: '2026-11-09', match_time: '21:00'},
    {match_id: 4, match_date: '2026-11-09', match_time: '19:00'},
    {match_id: 5, match_date: '2026-11-09', match_time: '23:30'},
    {match_id: 6, match_date: null}
  ];
  const matches = [{match_id: '4', home_sets: 3, away_sets: 0}];
  const fixtures = context.upcomingMatches({upcoming, matches}, new Date('2026-11-10T00:10:00Z'));
  assert.deepEqual(Array.from(fixtures, game => game.match_id), [3, 5, 2]);
});

test('rotation identifies the setter in the selected zone with no independent front/back toggle', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const code = source.slice(source.indexOf('function VolleyballCourt('), source.indexOf('function renderTeamsPage('));
  const context = {esc:x=>x, state:{rotation:4}}; vm.createContext(context); vm.runInContext(code, context);
  const html = context.VolleyballCourt({selected:4, homeLabel:'Equipe'});
  assert.match(html, /Levantadora na zona 4/);
  assert.match(html, /P4/);
  assert.doesNotMatch(html, /Levantadora no FUNDO/);
  const section = source.slice(source.indexOf('function renderTeamRotations('), source.indexOf('function renderTeamAttack('));
  assert.doesNotMatch(section, /setter-fundo|setter-rede/);
});

test('quick competition selection chooses an existing gender and never falls back to another gender', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const start = source.indexOf('function selectQuickCompetition(');
  assert.notEqual(start, -1, 'quick selector should exist');
  const code = source.slice(start, source.indexOf('// 12. RENDER PIPELINE', start));
  const cohorts = [
    {competition:'SUPERLIGA',category:'A',gender:'feminino',season:'2026-2027',edition_status:'CURRENT'},
    {competition:'SUPERLIGA',category:'A',gender:'masculino',season:'2025-2026'},
    {competition:'SUPERLIGA',category:'A',gender:'masculino',season:'2026-2027',edition_status:'CURRENT'},
    {competition:'CBS',category:'sub18',gender:'masculino',season:'2026'}
  ];
  const notice={textContent:'',hidden:true};
  const context={DATA:{cohorts}, state:{cohort:0,team:'old',matchId:1}, C(){return cohorts[this.state.cohort]}, $(s){return s==='#filter-notice'?notice:null},render(){}};
  context.C=()=>cohorts[context.state.cohort]; vm.createContext(context); vm.runInContext(code,context);
  context.selectQuickCompetition('SUPERLIGA','masculino');
  assert.equal(context.state.cohort,2);
  assert.equal(context.state.matchId,null);
  context.selectQuickCompetition('CBS','masculino');
  assert.equal(context.state.cohort,3);
  context.selectQuickCompetition('CBS','feminino');
  assert.equal(context.state.cohort,3);
  assert.match(notice.textContent,/CBS feminino.*não.*disponível/i);
  assert.equal(notice.hidden,false);
  context.selectQuickCompetition('SUPERLIGA','feminino');
  assert.equal(context.state.cohort,0);
  assert.equal(notice.hidden,true);
});

test('advanced filters offer only real gender and season combinations', () => {
  const source = fs.readFileSync('cbv/export/templates/atlas.js', 'utf8');
  const start = source.indexOf('function availableFilterChoices(');
  assert.notEqual(start, -1, 'dependent filter logic should exist');
  const code = source.slice(start, source.indexOf('// ADVANCED FILTERS BOTTOM SHEET', start));
  const context={compKey:c=>`${c.competition} · ${c.category}`}; vm.createContext(context); vm.runInContext(code,context);
  const rows=[
    {competition:'CBS',category:'sub18',gender:'masculino',season:'2026'},
    {competition:'SUPERLIGA',category:'A',gender:'feminino',season:'2026-2027',edition_status:'CURRENT'},
    {competition:'SUPERLIGA',category:'A',gender:'masculino',season:'2026-2027',edition_status:'CURRENT'},
    {competition:'SUPERLIGA',category:'A',gender:'masculino',season:'2025-2026'}
  ];
  let c=context.availableFilterChoices(rows,'SUPERLIGA · A','masculino','2026');
  assert.equal(c.gender,'masculino'); assert.equal(c.season,'2026-2027');
  c=context.availableFilterChoices(rows,'CBS · sub18','feminino','2026-2027');
  assert.equal(c.gender,'masculino'); assert.equal(c.season,'2026');
  assert.deepEqual(Array.from(c.genders),['masculino']);
});
