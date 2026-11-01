const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('cbv/export/templates/atlas.js','utf8');

test('advanced team view renders without missing functions', () => {
  const js = source.slice(source.indexOf('function renderTeamAdvanced('), source.indexOf('// 9. SCREEN 4'));
  const context={esc:String,num:String,pct:String};vm.createContext(context);vm.runInContext(js,context);
  assert.match(context.renderTeamAdvanced({team:'Equipe'},{serve_runs:{n:0}}),/Análise avançada/i);
});

test('athlete rows provide a real accessible profile action', () => {
  const js = source.slice(source.indexOf('function renderAthletesPage('), source.indexOf('// LAYERED ATHLETE PROFILE VIEW'));
  const context={athleteLoadState:new Map(), C:()=>({teams:[{team:'A',athletes:[{name:'Ana',points:4}]}]}),state:{athleteQuery:'',athleteName:null,athleteTeam:null},normalized:s=>s.toLowerCase(),competitionLabel:()=>'',esc:String,teamName:String,num:String,pct:String,renderAthleteProfile:a=>a.name};
  vm.createContext(context);vm.runInContext(js,context);
  assert.match(context.renderAthletesPage(),/data-open-athlete/);
});
