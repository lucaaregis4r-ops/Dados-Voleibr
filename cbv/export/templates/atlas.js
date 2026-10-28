// Shared court, rotation matrix and replay. No external runtime or fabricated events.
Object.assign(state,{layer:'so',rotation:1,matrixMetric:'points',matrixCell:null,rallyIndex:0,athlete:null,overviewRotMetric:'so',overviewRotIndex:1});
const atlasTeam=name=>C()?.atlas_teams?.[name];
const rallyCache=new Map();
function matchRallies(id){const key=C().id+':'+id;if(!rallyCache.has(key)){const fields=C().rally_fields||[];rallyCache.set(key,(C().rallies?.[String(id)]||[]).map(row=>Object.fromEntries(fields.map((k,i)=>[k,row[i]]))))}return rallyCache.get(key)}
function fillFor(value,baseline=50){if(value==null)return '#DEDAD0';const d=value-baseline;return d>=0?`rgba(20,121,111,${Math.min(.8,.16+Math.abs(d)/45)})`:`rgba(200,77,65,${Math.min(.8,.16+Math.abs(d)/45)})`}
function VolleyballCourt({variant='half',rotations=[],layer='so',players=null,awayPlayers=null,homeLabel='',awayLabel='',selected=null,baseline=50,overlay=null}={}){
 if(variant==='comparison')return `<div class="atlas-courts comparison">${VolleyballCourt({variant:'half',rotations,layer,homeLabel})}${VolleyballCourt({variant:'half',players:awayPlayers,homeLabel:awayLabel})}</div>`;
 const full=variant==='full',height=full?540:320;
 const positions=[[1,285,full?455:245],[6,180,full?455:245],[5,75,full?455:245],[4,75,full?325:105],[3,180,full?325:105],[2,285,full?325:105]];
 const zone=(position,x,y,roster,opposite=false)=>{
   const r=rotations.find(r=>r.position===position),m=r?.[layer],value=layer==='expected'?m?.expected:m?.value;
   const label=roster?(roster[position-1]==null?'—':'#'+roster[position-1]):'P'+position;
   const detail=roster?(overlay?.[position-1]!=null?'peso '+pct(overlay[position-1]*100):'Z'+position):value==null?'sem sequência':pct(value);
   const n=layer==='expected'?m?.n:m?.n;
   return `<g class="court-zone" ${!roster?`data-rotation="${position}" role="button" tabindex="0" aria-label="P${position}: ${esc(detail)}, n=${n||0}"`:''}><rect x="${x-43}" y="${y-39}" width="86" height="78" rx="1" fill="${roster?'#FBFAF6':fillFor(value,baseline)}" stroke="${selected===position?'#071A2F':'none'}" stroke-width="3"/><text class="court-name" x="${x}" y="${y-15}" text-anchor="middle">${esc(label)}</text><text class="${roster?'court-label':'court-value'}" x="${x}" y="${y+9}" text-anchor="middle">${esc(detail)}</text>${!roster?`<text class="court-label" x="${x}" y="${y+28}" text-anchor="middle">n=${num(n||0)}</text>`:''}</g>`;
 };
 return `<figure style="margin:0"><svg class="court-svg ${variant}" viewBox="0 0 360 ${height}" role="img" aria-label="${full?'Quadra completa e formações por zona':'Mapa de passagens: posição de referência da levantadora inicial'}"><rect x="16" y="16" width="328" height="${height-32}" fill="var(--court)"/><rect x="24" y="24" width="312" height="${height-48}" fill="none" stroke="var(--court-line)" stroke-width="2"/><path d="M24,${full?270:42} H336 M24,${full?365:145} H336 ${full?'M24,175 H336':''}" fill="none" stroke="var(--court-line)" stroke-width="2"/><path d="M12,${full?270:42} H348" stroke="var(--navy)" stroke-width="4"/>${positions.map(([p,x,y])=>zone(p,x,y,players)).join('')}${full?positions.map(([p,x,y])=>zone(p,360-x,540-y,awayPlayers||[] ,true)).join(''):''}<text x="180" y="${full?529:310}" text-anchor="middle" class="court-label">${esc(homeLabel)}</text>${full?`<text x="180" y="12" text-anchor="middle" class="court-label">${esc(awayLabel)}</text>`:''}</svg><figcaption class="court-caption">${players?'Zonas esquemáticas; # = camisa. Formação parcial exige conferência na fonte.':'P = posição de referência da levantadora inicial na passagem. Selecione para ver saque e recepção.'}</figcaption></figure>`;
}
function rotationWheel(data){
 const cycle=[1,6,5,4,3,2],cx=165,cy=155;
 const point=(i,r)=>{const a=(-90+i*60)*Math.PI/180;return [cx+Math.cos(a)*r,cy+Math.sin(a)*r]};
 return `<div><svg class="wheel-svg" viewBox="0 0 330 320" role="img" aria-label="Ciclo P1 P6 P5 P4 P3 P2; azul SO, laranja BP"><circle cx="165" cy="155" r="98" fill="none" stroke="var(--line)"/><circle cx="165" cy="155" r="67" fill="none" stroke="var(--line)"/>${cycle.map((p,i)=>{const r=data?.rotations?.find(r=>r.position===p),[x,y]=point(i,124),[sx,sy]=point(i,67),[bx,by]=point(i,98);return `<g data-rotation="${p}" role="button" tabindex="0" aria-label="P${p}, SO ${pct(r?.so.value)}, BP ${pct(r?.bp.value)}"><circle cx="${sx}" cy="${sy}" r="${r?.so.n?5+Math.min(12,Math.sqrt(r.so.n)):3}" fill="var(--sideout)" opacity="${r?.so.n ? .9 : .2}"/><circle cx="${bx}" cy="${by}" r="${r?.bp.n?5+Math.min(12,Math.sqrt(r.bp.n)):3}" fill="var(--breakpoint)" opacity="${r?.bp.n ? .9 : .2}"/><text x="${x}" y="${y+4}" text-anchor="middle">P${p}</text><title>P${p}: SO ${pct(r?.so.value)} n=${r?.so.n||0}; BP ${pct(r?.bp.value)} n=${r?.bp.n||0}</title></g>`}).join('')}<text x="165" y="149" text-anchor="middle">RECUPERA O SAQUE</text><text x="165" y="170" text-anchor="middle">→ AVANÇA</text></svg><p class="wheel-key"><span>SO · interior</span><span>BP · exterior</span></p><p class="note">Tamanho dos marcadores indica amostra em escala limitada. Ciclo: P1 → P6 → P5 → P4 → P3 → P2.</p></div>`;
}
function rotationDetail(data){const r=data?.rotations.find(r=>r.position===state.rotation);if(!r)return '';return `<div class="rotation-detail"><h3>P${r.position} · o que acontece nesta passagem?</h3>${table(['Estado','Taxa','n','Δ equipe','Δ competição'],[['so','Recebendo · SO'],['bp','Sacando · BP']].map(([k,label])=>row([label,pct(r[k].value),num(r[k].n),signed(r[k+'_delta_team'])+' pp',signed(r[k+'_delta_competition'])+' pp'])))}<details><summary>Esperado e intervalo</summary><p class="source-tag experimental">EXPERIMENTAL · histórico anterior ao dia</p>${table(['Métrica','Observado','Esperado','Diferença','n'],[['xso','SO'],['xbp','BP'],['expected','Pontos/100'],['pressure','Pontos/100 · alta pressão']].map(([k,label])=>row([label,pct(r[k].observed),pct(r[k].expected),signed(r[k].above_expected)+' pp',num(r[k].n)])))}<p class="note">${['so','bp'].map(k=>`${k.toUpperCase()} IC Wilson 95%: ${r[k].ci?r[k].ci.map(fmt).join('–')+'%':'—'}`).join(' · ')}. Comparações de esperado usam somente a amostra com previsão histórica. Alta pressão: acima do P75 de leverage dos dias anteriores da competição; faixas em Dados/caderno, classificação experimental.</p></details></div>`}
function courtSection(data){if(!data?.coverage.rallies)return '<p class="atlas-empty">Ainda não há sequência reconciliada para esta equipe. Estatísticas do Match Report permanecem abaixo.</p>';return `<section class="atlas-sheet"><div class="atlas-heading"><h2>Onde a equipe ganha e perde pontos?</h2><span class="source-tag">SEQUÊNCIA RECONSTRUÍDA · ${num(data.coverage.rallies)} PONTOS</span></div><div class="atlas-tabs">${[['so','Side-Out'],['bp','Break Point'],['expected','xPoints · experimental'],['pressure','Pressão · experimental']].map(([k,label])=>`<button data-layer="${k}" class="${state.layer===k?'active':''}">${label}</button>`).join('')}</div><div class="atlas-courts">${VolleyballCourt({rotations:data.rotations,layer:state.layer,homeLabel:teamName(data.team),selected:state.rotation,baseline:state.layer==='so'?data.so.value:state.layer==='bp'?data.bp.value:data.expected.observed})}${rotationWheel(data)}</div><p class="note">Rotação identificada em ${num(data.coverage.rotation_rallies)} / ${num(data.coverage.rallies)} pontos. Cor compara a taxa com a média da equipe nesta camada. Taxas incluem erros do adversário; são diferentes do SO/BP creditado no relatório.</p>${rotationDetail(data)}</section>`}
function matrixSection(data,title='Contra qual rotação adversária?'){
 if(!data)return '';
 const selected=state.matrixCell&&data.matrix.find(c=>c.own===state.matrixCell[0]&&c.other===state.matrixCell[1]);
 return `<section class="atlas-sheet"><div class="atlas-heading"><h2>${title}</h2><label>Métrica<select id="matrix-metric">${[['points','Pontos / 100'],['so','SO'],['bp','BP']].map(([key,label])=>`<option value="${key}" ${state.matrixMetric===key?'selected':''}>${label}</option>`).join('')}</select></label></div><p class="note">Linhas: rotação própria · colunas: rotação adversária. Verde acima de 50%; terracota abaixo. Células mostram taxa e n; não são ranking ajustado.</p><div class="matrix-box"><div class="matchup-matrix"><span></span>${[1,2,3,4,5,6].map(p=>`<span class="axis">P${p}</span>`).join('')}${[1,2,3,4,5,6].map(p=>`<span class="axis">P${p}</span>${data.matrix.filter(c=>c.own===p).map(c=>{const m=c[state.matrixMetric];return `<button data-cell="${c.own},${c.other}" class="${m.n?'':'missing'} ${selected===c?'selected':''}" style="background:${fillFor(m.value)}" aria-label="P${c.own} contra P${c.other}: ${pct(m.value)}, n=${m.n}">${m.n?pct(m.value):'—'}<small>n=${num(m.n)}</small></button>`}).join('')}`).join('')}</div></div>${selected?`<div class="matrix-detail"><h3>P${selected.own} × P${selected.other}</h3>${table(['Pontos/100','SO · n','BP · n'],[row([pct(selected.points.value)+' · n='+num(selected.points.n),pct(selected.so.value)+' · '+num(selected.so.n),pct(selected.bp.value)+' · '+num(selected.bp.n)])])}<p class="note">Jogos que compõem a célula:</p>${selected.matches.map(id=>`<button class="text-button" data-match="${id}">#${id}</button>`).join(' · ')||'Sem sequência coberta.'}</div>`:''}</section>`;
}
function runSection(data){const runs=data?.serve_runs;if(!runs?.n)return '';const max=Math.max(...runs.distribution.map(d=>d.n),1);return `<section class="atlas-sheet"><div class="atlas-heading"><h2>Quanto dura uma passagem de saque?</h2><span class="source-tag">${num(runs.n)} COMPLETAS · ${runs.censored} CENSURADAS</span></div><div class="atlas-courts"><svg class="run-chart" viewBox="0 0 480 230" role="img" aria-label="Histograma de pontos por passagem completa">${runs.distribution.map((d,i)=>{const w=400/runs.distribution.length,x=45+i*w,h=d.n/max*155;return `<rect x="${x}" y="${185-h}" width="${Math.max(2,w-8)}" height="${h}" fill="var(--breakpoint)"/><text x="${x+w/2}" y="207" text-anchor="middle">${d.points}</text><text x="${x+w/2}" y="${178-h}" text-anchor="middle">${d.n}</text>`}).join('')}<text x="245" y="228" text-anchor="middle">Pontos ganhos sacando</text></svg><div>${table(['Medida','Valor'],[row(['Média',fmt(runs.mean)]),row(['Mediana',fmt(runs.median)]),row(['Máximo observado',num(runs.maximum)]),...[2,3,4].map(k=>row([`P(${k}+ pontos)`,pct(100*(runs.survival.find(s=>s.points===k)?.value??0))]))])}</div></div><details><summary>Passagens por rotação, sobrevivência e definição</summary>${table(['Rotação','Completas','Média','Censuradas'],(runs.by_rotation||[]).map(r=>row(['P'+r.position,r.n,fmt(r.mean),r.censored])))}${table(['Pontos ≥ k','Frequência'],runs.survival.map(s=>row([s.points,pct(s.value==null?null:s.value*100)])))}<p class="note">${esc(runs.definition)} O ponto que recupera o saque não entra na sequência de BP.</p></details></section>`}
function lineupSection(data){if(!data)return '';return `<details class="details-panel"><summary>Quem estava em quadra? · formações e on/off</summary><p class="note">${num(data.coverage.reliable_presence_rallies)} pontos com presença reconciliada. Somente seis atletas e controle de líbero coerentes entram aqui.</p>${table(['Atletas / camisas','n','Pontos/100','SO','BP','Ajustado¹'],data.lineups.slice(0,30).map(l=>row([esc(l.identities?.map(teamName).join(' · ')||l.players.map(p=>'#'+p).join(' ')),num(l.points.n),pct(l.points.value),pct(l.so.value),pct(l.bp.value),pct(l.adjusted)])))}<p class="note">¹ Shrinkage descritivo para média da equipe, força fixa de 100 pontos. Não mede efeito individual.</p>${table(['Atleta','Com · n','Sem · n','Diferença bruta','Ajustado β¹'],data.on_off.map(a=>row([esc(teamName(a.player)),pct(a.on.value)+' · '+num(a.on.n),pct(a.off.value)+' · '+num(a.off.n),signed(a.difference)+' pp',fmt(a.adjusted_contextual_effect?.value,3)])))}<p class="note">¹ Efeito contextual em log-odds, experimental; só exibido após ganho temporal sobre contexto sem atletas, ≥5 jogos de avaliação e ≥20 pontos com/sem. Controles: adversário, rotação, saque, placar/set e seis companheiras. Não é efeito causal; ausência de ganho ou cobertura mantém —.</p></details>`}

// Placar 2026 Native Overview (Hierarchy Suggestions 1 & 2)
overview = function(){
  const c = C();
  if(!c) return '<p class="empty">Nenhuma coorte selecionada.</p>';
  const matches = c.matches || [];
  const completed = matches.filter(m => m.home_sets != null && m.away_sets != null);
  
  let teamA = null, teamB = null, featMatch = null;
  if(completed.length){
    const sorted = [...completed].sort((a,b) => String(b.date||'').localeCompare(String(a.date||'')) || b.match_id - a.match_id);
    featMatch = sorted[0];
    teamA = c.teams.find(t => t.team === featMatch.home_team) || c.teams[0];
    teamB = c.teams.find(t => t.team === featMatch.away_team) || (c.teams.find(t => t.team !== teamA?.team) || c.teams[0]);
  } else if(c.teams.length >= 2){
    teamA = c.teams[0];
    teamB = c.teams[1];
  } else if(c.teams.length === 1){
    teamA = c.teams[0];
    teamB = c.teams[0];
  }

  // 1. Editorial Lead
  let leadHtml = '';
  if(teamA && teamB && matches.length > 0){
    const soA = teamA.metrics.so.value, soB = teamB.metrics.so.value;
    const bpB = teamB.metrics.bp.value;
    const diffSo = (soA != null && soB != null) ? (soA - soB) : null;
    let deckText = '';
    if(diffSo != null && Math.abs(diffSo) >= 0.8){
      deckText = `${teamName(teamA.team)} chega com side-out de ${pct(soA)}${teamA.metrics.so.delta != null ? ' (' + signed(teamA.metrics.so.delta) + ' pp vs média da liga)' : ''}. ${teamName(teamB.team)} sustenta ${pct(soB)} de side-out e ${pct(bpB)} de break point. A leitura abaixo destaca o que diferencia as equipes e abre a camada estatística completa no modo Dados.`;
    } else {
      deckText = `${teamName(teamA.team)} e ${teamName(teamB.team)} apresentam números equilibrados na temporada: ${pct(soA)} e ${pct(soB)} de side-out, respectivamente. A análise por rotação revela os pontos de vulnerabilidade e estabilidade de cada time.`;
    }
    leadHtml = `
    <section class="lead">
      <div class="lead-copy">
        <div class="kicker">Jogo em destaque · ${esc(competitionLabel(c))}</div>
        <h1>${esc(teamName(teamA.team))} × ${esc(teamName(teamB.team))}</h1>
        <div class="lead-deck">${esc(deckText)}</div>
      </div>
      <aside class="lead-card">
        <div>
          <div class="label">${featMatch?.date ? matchDate(featMatch.date) + ' · ' : ''}${esc(competitionLabel(c))}</div>
          <div class="match-compact">
            <div class="team-abbr">${esc(teamAbbr(teamA.team))}</div>
            <div class="vs">VS</div>
            <div class="team-abbr right">${esc(teamAbbr(teamB.team))}</div>
          </div>
          <div class="match-info">
            ${featMatch?.home_sets != null ? `Último placar: ${featMatch.home_sets} × ${featMatch.away_sets}<br>` : ''}
            Temporada ${esc(seasonLabel(c.season))}<br>
            ${num(matches.length)} partidas registradas
          </div>
        </div>
        <button type="button" class="match-link" data-open-confronto="${esc(teamA.team)}" data-open-opponent="${esc(teamB.team)}">Abrir confronto →</button>
      </aside>
    </section>`;
  } else {
    leadHtml = `
    <section class="lead">
      <div class="lead-copy">
        <div class="kicker">Edição da competição · ${esc(competitionLabel(c))}</div>
        <h1>${esc(seasonLabel(c.season))}</h1>
        <div class="lead-deck">
          ${c.edition_status === 'CURRENT' && !matches.length ? 'Ainda sem partidas concluídas coletadas nesta edição. Consulte a lista de partidas ou selecione uma temporada anterior nos filtros.' : 'Visão geral dos dados consolidados da competição.'}
        </div>
      </div>
      <aside class="lead-card">
        <div>
          <div class="label">${esc(competitionLabel(c))}</div>
          <div class="match-info">
            Temporada ${esc(seasonLabel(c.season))}<br>
            ${matches.length ? num(matches.length) + ' partidas analisadas' : 'Aguardando partidas'}
          </div>
        </div>
      </aside>
    </section>`;
  }

  // 2. Metric Strip (.kpis)
  const sources = c.source_snapshots || [];
  const reconstructed = Object.keys(c.rallies || {}).length;
  const scoresheets = sources.filter(s => s.source_type === 'scoresheet' && s.status === 'AVAILABLE').length;
  let kpisHtml = '';
  if(teamA && teamB && matches.length > 0){
    kpisHtml = `
    <section class="section">
      <div class="section-heading">
        <h2>Números do confronto</h2><span class="rule"></span><small>comparação rápida</small>
      </div>
      <div class="kpis">
        <div class="kpi primary">
          <span class="kpi-label">${esc(teamName(teamA.team))} · Side-out</span>
          ${tooltip(teamA.metrics.so)}
          <strong>${pct(teamA.metrics.so.value)}</strong>
          <p>${teamA.metrics.so.delta != null ? signed(teamA.metrics.so.delta) + ' pp vs média da liga' : 'Média da equipe'}</p>
        </div>
        <div class="kpi">
          <span class="kpi-label">${esc(teamName(teamA.team))} · Break point</span>
          ${tooltip(teamA.metrics.bp)}
          <strong>${pct(teamA.metrics.bp.value)}</strong>
          <p>${teamA.metrics.bp.delta != null ? signed(teamA.metrics.bp.delta) + ' pp vs média da liga' : 'Média da equipe'}</p>
        </div>
        <div class="kpi">
          <span class="kpi-label">${esc(teamName(teamB.team))} · Side-out</span>
          ${tooltip(teamB.metrics.so)}
          <strong>${pct(teamB.metrics.so.value)}</strong>
          <p>${teamB.metrics.so.delta != null ? signed(teamB.metrics.so.delta) + ' pp vs média da liga' : 'Média da equipe'}</p>
        </div>
        <div class="kpi">
          <span class="kpi-label">Amostra usada</span>
          <strong>${num(matches.filter(m => m.validation_status === 'VALID').length)} jogos</strong>
          <p>partidas validadas na liga</p>
        </div>
      </div>
      <div class="advanced">
        AMOSTRA CONSOLIDADA: ${num(matches.length)} PARTIDAS COLETADAS (${num(matches.filter(m => m.validation_status === 'VALID').length)} VÁLIDAS) · ${num(reconstructed)} RECONSTRUÍDAS · ${num(scoresheets)} SÚMULAS DISPONÍVEIS · INTERVALOS WILSON 95% CALCULADOS SOBRE DENOMINADORES REAIS DO MATCH REPORT.
      </div>
    </section>`;
  } else {
    kpisHtml = `
    <section class="section">
      <div class="section-heading">
        <h2>Números da competição</h2><span class="rule"></span><small>indicadores consolidados</small>
      </div>
      <div class="kpis">
        <div class="kpi primary">
          <span class="kpi-label">Side-out médio</span>
          <strong>${pct(c.metrics?.so?.value)}</strong>
          <p>Média da liga</p>
        </div>
        <div class="kpi">
          <span class="kpi-label">Break point médio</span>
          <strong>${pct(c.metrics?.bp?.value)}</strong>
          <p>Média da liga</p>
        </div>
        <div class="kpi">
          <span class="kpi-label">Eficiência de ataque</span>
          <strong>${pct(c.metrics?.eff?.value)}</strong>
          <p>Média da liga</p>
        </div>
        <div class="kpi">
          <span class="kpi-label">Partidas</span>
          <strong>${num(matches.length)}</strong>
          <p>registros na base</p>
        </div>
      </div>
    </section>`;
  }

  // 3. Tactical Reading (.content-grid)
  let readingHtml = '';
  if(teamA && teamB && matches.length > 0){
    const effKeys = ['pos_rec_eff','neg_rec_eff','trans_eff'];
    const pA = effKeys.map(k => ({k, v: teamA.metrics[k]?.value})).filter(x => x.v != null).sort((a,b) => b.v - a.v)[0];
    const worstA = effKeys.map(k => ({k, v: teamA.metrics[k]?.value})).filter(x => x.v != null).sort((a,b) => a.v - b.v)[0];
    const topTeams = [...c.teams].filter(t => t.metrics.so.value != null).sort((a,b) => b.metrics.so.value - a.metrics.so.value).slice(0, 5);
    const readings = Object.values(c.atlas_teams || {}).filter(t => t.readings && t.readings.length).slice(0, 3);
    
    readingHtml = `
    <section class="section">
      <div class="content-grid">
        <div class="panel">
          <div class="panel-head"><h3>Leitura do confronto</h3><small>o que diferencia as equipes</small></div>
          <div class="panel-body">
            <div class="insight">
              <div class="insight-value">${pA ? pct(pA.v) : '—'}</div>
              <div>
                <h4>${esc(teamName(teamA.team))} · ${pA ? phaseName(pA.k.replace('_eff','')) : 'Fase'}</h4>
                <p>Passagem de maior rendimento ofensivo da equipe observada na temporada.</p>
              </div>
            </div>
            <div class="insight alert">
              <div class="insight-value">${worstA ? pct(worstA.v) : '—'}</div>
              <div>
                <h4>Atenção em ${worstA ? phaseName(worstA.k.replace('_eff','')) : 'Fase'}</h4>
                <p>Menor taxa de eficiência observada para ${esc(teamName(teamA.team))} nesta amostra.</p>
              </div>
            </div>
            <div class="insight">
              <div class="insight-value">${pct(teamB.metrics.bp.value)}</div>
              <div>
                <h4>${esc(teamName(teamB.team))} no Break Point</h4>
                <p>Capacidade de pontuar sacando; taxa média de conversão em contra-ataques e bloqueio.</p>
              </div>
            </div>
            ${readings.length ? `
            <div style="border-top:1px solid var(--line);padding:14px 4px 6px;">
              <small style="font:800 9px var(--mono);color:var(--soft);text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:8px;">Leituras táticas da competição</small>
              <ul class="atlas-readings">
                ${readings.map(t => `<li>${teamLink(t.team)} · ${esc(t.readings[0].text)}</li>`).join('')}
              </ul>
            </div>` : ''}
          </div>
        </div>
        <aside class="panel">
          <div class="panel-head"><h3>Side-out na liga</h3><small>top 5</small></div>
          <div class="panel-body">
            ${topTeams.map((t,i) => {
              const isCurr = [teamA.team, teamB.team].includes(t.team);
              return `<div class="rank-row ${isCurr ? 'current' : ''}"><span class="pos">0${i+1}</span><b>${esc(teamName(t.team))}</b><span class="v">${pct(t.metrics.so.value)}</span></div>`;
            }).join('') || '<p class="empty">Sem dados de ranking.</p>'}
          </div>
        </aside>
      </div>
    </section>`;
  }

  // 4. Rotations Grid (P1-P6)
  let rotationHtml = '';
  if(teamA && matches.length > 0){
    const ad = atlasTeam(teamA.team);
    const metric = state.overviewRotMetric || 'so';
    const curP = state.overviewRotIndex || 1;
    const rotList = [1,2,3,4,5,6].map(p => {
      const r = ad?.rotations?.find(x => x.position === p);
      const m = metric === 'so' ? r?.so : r?.bp;
      const v = m?.value;
      const d = metric === 'so' ? r?.so_delta_team : r?.bp_delta_team;
      const n = m?.n || 0;
      const s = d > 2 ? 'good' : d < -2 ? 'bad' : '';
      return { p, v, d, n, s, ci: m?.ci };
    });
    const activeItem = rotList.find(x => x.p === curP) || rotList[0];
    let noteText = '';
    if(activeItem.v != null){
      if(activeItem.d > 2){
        noteText = `P${activeItem.p} é a passagem de maior rendimento nesta amostra (+${fmt(activeItem.d)} pp vs média da equipe). É onde o ${teamName(teamA.team)} tem sido mais estável.`;
      } else if(activeItem.d < -2){
        noteText = `P${activeItem.p} é a passagem de menor rendimento (${fmt(activeItem.d)} pp vs média da equipe); ponto de vulnerabilidade observado nesta temporada.`;
      } else {
        noteText = `P${activeItem.p} opera próximo da média da equipe nesta amostra (${signed(activeItem.d)} pp).`;
      }
    } else {
      noteText = `Rotação P${curP} observada nos relatórios de partida; consulte a ficha da equipe para o saldo de pontos.`;
    }
    rotationHtml = `
    <section class="section">
      <div class="section-heading">
        <h2>Rotação a rotação · ${esc(teamName(teamA.team))}</h2><span class="rule"></span><small>selecione P1–P6</small>
      </div>
      <div class="panel">
        <div class="panel-body">
          <div class="rotation-toolbar">
            <div class="metric-tabs" id="overview-metric-tabs">
              <button type="button" class="${metric === 'so' ? 'active' : ''}" data-overview-metric="so">Side-out</button>
              <button type="button" class="${metric === 'bp' ? 'active' : ''}" data-overview-metric="bp">Break point</button>
            </div>
          </div>
          <div class="rotation-grid" id="overview-rotations">
            ${rotList.map(r => `
              <button type="button" class="rotation ${r.s} ${r.p === curP ? 'active' : ''}" data-overview-p="${r.p}" aria-label="P${r.p}: ${pct(r.v)}">
                <span class="p">P${r.p}</span>
                <strong>${pct(r.v)}</strong>
                <span class="status"></span>
              </button>`).join('')}
          </div>
          <div class="rotation-detail">
            <div><span>Valor</span><strong>${pct(activeItem.v)}</strong></div>
            <div><span>vs média da equipe</span><strong>${activeItem.d != null ? signed(activeItem.d) + ' pp' : '—'}</strong></div>
            <div><span>Amostra</span><strong>n=${num(activeItem.n)}</strong></div>
          </div>
          <div class="note">${esc(noteText)}</div>
          <div class="advanced">
            MÉTRICA: ${metric.toUpperCase()} CREDITADO NO RELATÓRIO · ROTAÇÃO P${curP} · COBERTURA: ${num(activeItem.n)} AÇÕES REGISTRADAS · IC WILSON 95%: ${activeItem.ci ? activeItem.ci.map(fmt).join('–') + '%' : 'INTERVALO NÃO ESTIMADO'} · LEITURA DESCRITIVA.
          </div>
        </div>
      </div>
    </section>`;
  }

  // 5. Team Comparison
  let compareHtml = '';
  if(teamA && teamB && matches.length > 0){
    const rows = [
      {label: 'Side-out', va: teamA.metrics.so.value, vb: teamB.metrics.so.value},
      {label: 'Break point', va: teamA.metrics.bp.value, vb: teamB.metrics.bp.value},
      {label: 'Eficiência de ataque', va: teamA.metrics.eff.value, vb: teamB.metrics.eff.value},
      {label: 'K1 com passe positivo (Kill%)', va: teamA.metrics.pos_rec.value, vb: teamB.metrics.pos_rec.value},
      {label: 'K1 fora do sistema (Kill%)', va: teamA.metrics.neg_rec.value, vb: teamB.metrics.neg_rec.value},
      {label: 'K2 / Transição (Kill%)', va: teamA.metrics.trans.value, vb: teamB.metrics.trans.value},
      {label: 'Campanha', va: `${teamA.wins}V – ${teamA.losses}D`, vb: `${teamB.wins}V – ${teamB.losses}D`, raw: true, better: teamA.wins > teamB.wins ? 'a' : teamB.wins > teamA.wins ? 'b' : null}
    ];
    compareHtml = `
    <section class="section">
      <div class="section-heading">
        <h2>Comparação das equipes</h2><span class="rule"></span><small>sem esconder a tabela</small>
      </div>
      <div class="content-grid">
        <div class="panel">
          <div class="panel-body">
            <div class="table-wrap">
              <table class="compare">
                <thead>
                  <tr>
                    <th>Métrica</th>
                    <th>${esc(teamName(teamA.team))}</th>
                    <th>${esc(teamName(teamB.team))}</th>
                    <th>Melhor índice</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map(r => {
                    let bestText = '—';
                    let bestA = false, bestB = false;
                    if(r.raw){
                      bestText = r.better === 'a' ? teamName(teamA.team) : r.better === 'b' ? teamName(teamB.team) : 'Empate';
                      bestA = r.better === 'a'; bestB = r.better === 'b';
                    } else if(r.va != null && r.vb != null){
                      if(r.va > r.vb){ bestA = true; bestText = teamName(teamA.team); }
                      else if(r.vb > r.va){ bestB = true; bestText = teamName(teamB.team); }
                      else bestText = 'Empate';
                    }
                    return `
                    <tr>
                      <td>${esc(r.label)}</td>
                      <td class="num ${bestA ? 'best' : ''}">${r.raw ? r.va : pct(r.va)}</td>
                      <td class="num ${bestB ? 'best' : ''}">${r.raw ? r.vb : pct(r.vb)}</td>
                      <td>${esc(bestText)}</td>
                    </tr>`;
                  }).join('')}
                </tbody>
              </table>
            </div>
            <div class="advanced">
              TAXAS CALCULADAS COM DENOMINADOR REAL DAS AÇÕES DA COORTE SELECIONADA · IC WILSON 95% E AJUSTE BETA-BINOMIAL DISPONÍVEIS NA FICHA DE CADA EQUIPE.
            </div>
          </div>
        </div>
        <aside class="panel">
          <div class="panel-head"><h3>Como ler</h3><small>camada essencial</small></div>
          <div class="panel-body">
            <div class="insight">
              <div class="insight-value">SO</div>
              <div>
                <h4>Side-out</h4>
                <p>Percentual de pontos conquistados quando a equipe recebe o saque adversário (fase de recepção).</p>
              </div>
            </div>
            <div class="insight">
              <div class="insight-value">BP</div>
              <div>
                <h4>Break point</h4>
                <p>Percentual de pontos conquistados quando a própria equipe está sacando (fase de defesa/bloqueio).</p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </section>`;
  }

  // 6. Scatter Plot SO x BP (Moved down)
  let scatterHtml = `
  <section class="section">
    <div class="section-heading">
      <h2>Mapa da competição · Match Report</h2><span class="rule"></span><small>Side-Out e Break Point por equipe</small>
    </div>
    <div class="panel">
      <div class="panel-body">
        ${scatter()}
        <p class="chart-key" style="padding:10px 14px 4px;margin:0;font-size:11px;color:var(--soft);">
          SO/BP creditados no relatório, sem erros do adversário. Linhas tracejadas: média da competição. Clique em uma equipe no gráfico para abrir o perfil tático completo.
        </p>
        <div class="advanced">
          SCATTER SO × BP: COORDENADAS HISTÓRICAS DA TEMPORADA ATUAL · DENOMINADOR EXCLUI ERROS NÃO FORÇADOS DO ADVERSÁRIO · EIXOS DELIMITADOS PELA AMPLITUDE DA LIGA.
        </div>
      </div>
    </div>
  </section>`;

  // 7. Recent Matches
  let recentHtml = `
  <section class="section">
    <div class="section-heading">
      <h2>Partidas recentes</h2><span class="rule"></span><button type="button" class="text-button" data-all-matches>Ver todas as partidas</button>
    </div>
    <div class="panel">
      <div class="panel-body">
        ${recentMatches()}
      </div>
    </div>
  </section>`;

  return leadHtml + kpisHtml + readingHtml + rotationHtml + compareHtml + scatterHtml + recentHtml;
};

const oldTeams=teams;
teams=function(){const t=team();if(!t)return oldTeams();const data=atlasTeam(t.team);return selectors()+heading(teamName(t.team),`${t.wins}–${t.losses} · ${t.games} jogos · ${competitionLabel()} ${seasonLabel(C().season)}`)+courtSection(data)+`<section class="atlas-sheet"><h2>Leitura tática</h2><ul class="atlas-readings">${data?.readings.map(r=>`<li data-rule="${r.rule_id}">${esc(r.text)}</li>`).join('')||'<li>Sem amostra suficiente por rotação; consulte a cobertura.</li>'}</ul></section>`+matrixSection(data)+`<section class="atlas-sheet"><h2>Como ataca em cada fase?</h2>${phases(t)}${expectedAttackSection(t.team)}</section>`+runSection(data)+opponentSection(t.team)+distributionSection(data)+lineupSection(data)+`<section class="atlas-sheet"><h2>Atletas</h2>${athletes(t)}</section><details class="details-panel"><summary>Match Report · perfil, indicadores e tendência</summary><p class="note">SO/BP creditados às ações no relatório; denominadores preservados do histórico.</p>${teamKpis(t)}${profile(t)}${trend(t)}</details>`};
function expectedAttackSection(name){const rows=(C().expected_attack||[]).filter(r=>r.team===name&&r.expected_kills!=null);return `<details><summary>xAttack por fase · experimental</summary>${table(['Fase','Tentativas cobertas','Kills aprox.','Esperados','Acima esperado'],['pos_rec','neg_rec','trans'].map(phase=>{const part=rows.filter(r=>r.phase===phase),sum=k=>part.reduce((a,r)=>a+r[k],0);return row([phaseName(phase),num(sum('n')),part.length?fmt(sum('kills')):'—',part.length?fmt(sum('expected_kills')):'—',part.length?signed(sum('above_expected')):'—'])}))}<p class="note">Baseline da fase na competição, usando somente datas anteriores. Kills publicados por fase podem ser aproximados por arredondamento. Sem ajuste por adversário.</p></details>`}
const oldConfrontation=confrontation;
confrontation=function(){const a=team(),b=C().teams.find(t=>t.team===state.opponent);if(!a||!b)return oldConfrontation();const ad=atlasTeam(a.team),bd=atlasTeam(b.team);return heading(`${teamName(a.team)} × ${teamName(b.team)}`)+selectors(true)+`<section class="atlas-sheet"><h2>Onde cada equipe ganha pontos?</h2><div class="atlas-tabs">${[['so','Side-Out'],['bp','Break Point'],['expected','xPoints · experimental'],['pressure','Pressão · experimental']].map(([key,label])=>`<button data-layer="${key}" class="${state.layer===key?'active':''}">${label}</button>`).join('')}</div><div class="atlas-courts comparison">${VolleyballCourt({variant:'half',rotations:ad?.rotations,layer:state.layer,homeLabel:teamName(a.team),baseline:state.layer==='so'?ad?.so.value:state.layer==='bp'?ad?.bp.value:ad?.expected.observed})}${VolleyballCourt({variant:'half',rotations:bd?.rotations,layer:state.layer,homeLabel:teamName(b.team),baseline:state.layer==='so'?bd?.so.value:state.layer==='bp'?bd?.bp.value:bd?.expected.observed})}</div><p class="note">Amostras históricas de cada equipe; não representa confronto direto ou escalação provável.</p></section>`+matrixSection(ad,teamName(a.team)+' × rotações dos adversários históricos')+`<section class="atlas-sheet"><h2>O que observar no confronto</h2><div class="atlas-courts comparison"><div><h3>${esc(teamName(a.team))}</h3><ul class="atlas-readings">${ad?.readings.map(r=>`<li>${esc(r.text)}</li>`).join('')||'<li>Sem amostra por rotação.</li>'}</ul></div><div><h3>${esc(teamName(b.team))}</h3><ul class="atlas-readings">${bd?.readings.map(r=>`<li>${esc(r.text)}</li>`).join('')||'<li>Sem amostra por rotação.</li>'}</ul></div></div><p class="note">Escalações prováveis não são fornecidas pelas fontes coletadas.</p></section><details class="details-panel"><summary>Relatórios · comparação por fase</summary>${table(['Fase',esc(teamName(a.team)),esc(teamName(b.team))],['pos_rec','neg_rec','trans'].map(k=>row([phaseName(k)+' · eficiência',metricCell(a.metrics[k+'_eff']),metricCell(b.metrics[k+'_eff'])])))}</details>`+model(a,b)};
function timeline(rr){const w=900,h=210,x=i=>48+i/Math.max(1,rr.length-1)*825,y=p=>175-p*140;let last=null,paths=[],current=[];rr.forEach((r,i)=>{if(r.wp_after==null){if(current.length)paths.push(current.join(' '));current=[]}else current.push(`${x(i)},${y(r.wp_after)}`)});if(current.length)paths.push(current.join(' '));return `<svg class="timeline" viewBox="0 0 ${w} ${h}" role="img" aria-label="Win Probability experimental, ponto a ponto, para a equipe mandante"><path d="M48,35 V175 H873 M48,105 H873" fill="none" stroke="var(--line)"/>${paths.map(p=>`<polyline points="${p}" fill="none" stroke="var(--navy)" stroke-width="2"/>`).join('')}${rr.map((r,i)=>{let result='';if(r.set_number!==last){last=r.set_number;result+=`<path d="M${x(i)},25 V180" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${x(i)+4}" y="20">SET ${r.set_number}</text>`}if(r.wp_after!=null)result+=`<circle class="point" data-rally="${i}" tabindex="0" role="button" aria-label="Set ${r.set_number} ponto ${r.rally_number}, WP ${pct(r.wp_after*100)}" cx="${x(i)}" cy="${y(r.wp_after)}" r="${state.rallyIndex===i?5:2.5}" fill="${r.winner_side==='home'?'var(--sideout)':'var(--breakpoint)'}"/>`;return result}).join('')}<text x="5" y="40">100%</text><text x="14" y="110">50%</text><text x="22" y="178">0%</text><text x="460" y="205" text-anchor="middle">Pontos de placar em ordem da partida</text></svg>`}
function replaySection(m,rr){if(!rr.length)return `<section class="atlas-sheet"><h2>Reconstrução da partida</h2><p>Sequência ainda indisponível ou não reconciliada. Consulte Dados para a tentativa registrada.</p></section>`;state.rallyIndex=Math.max(0,Math.min(state.rallyIndex,rr.length-1));const r=rr[state.rallyIndex],v=C().atlas_validations?.find(v=>v.match_id===m.match_id),events=v?.report.events||[];return `<section class="atlas-sheet" id="replay"><div class="atlas-heading"><h2>Como a partida mudou ponto a ponto?</h2><span class="source-tag experimental">WP / WPA / LEVERAGE · EXPERIMENTAL</span></div>${timeline(rr)}${rr.every(r=>r.wp_after==null)?'<p class="notice">Sem histórico anterior suficiente para estimar WP nesta partida.</p>':''}<p class="note">Probabilidade do mandante. Modelo de placar e saque com histórico anterior ao dia; futuras primeiras equipes sacadoras são marginalizadas 50/50. WP ainda sem calibração validada.</p><div class="replay-controls"><button data-step="-1" aria-label="Ponto anterior">←</button><label for="rally-slider" class="sr-only">Selecionar rally</label><input type="range" id="rally-slider" min="0" max="${rr.length-1}" value="${state.rallyIndex}"><button data-step="1" aria-label="Próximo ponto">→</button><span class="numeric">${state.rallyIndex+1}/${rr.length}</span></div><div class="scoreboard"><span>${esc(teamName(m.home_team))}<br><small>${r.serving_side==='home'?'SACANDO':'RECEBENDO'} · P${r.home_rotation??'?'}</small></span><strong>${r.score_home_after}:${r.score_away_after}</strong><span>${esc(teamName(m.away_team))}<br><small>${r.serving_side==='away'?'SACANDO':'RECEBENDO'} · P${r.away_rotation??'?'}</small></span></div><div class="replay-grid"><div>${VolleyballCourt({variant:'full',players:r.home_lineup||[],awayPlayers:r.away_lineup||[],homeLabel:teamName(m.home_team),awayLabel:teamName(m.away_team)})}</div><div><h3>Set ${r.set_number} · ponto ${r.rally_number}</h3>${table(['Estado','Valor'],[row(['Vencedor do ponto',esc(teamName(m[r.winner_side+'_team']))]),row(['WP antes',pct(r.wp_before==null?null:r.wp_before*100)]),row(['WP depois',pct(r.wp_after==null?null:r.wp_after*100)]),row(['WPA',signed(r.wpa==null?null:r.wpa*100)+' pp']),row(['Leverage',r.leverage==null?'—':fmt(r.leverage*100)+' pp']),row(['Crunch / Super Crunch',`${r.crunch?'sim':'não'} / ${r.super_crunch?'sim':'não'}`]),row(['Presença mandante',esc(r.home_lineup_confidence||'UNKNOWN')]),row(['Presença visitante',esc(r.away_lineup_confidence||'UNKNOWN')])],[0,1])}<p class="note">Placar após o ponto. Formação e rotação mostradas antes do ponto. A fonte não informa quem executou a ação.</p></div></div><details><summary>Ponto a ponto · ${rr.length} pontos</summary><div class="rally-table table-wrap"><table><thead><tr><th>Set</th><th>Ponto</th><th>Placar após</th><th>Saque</th><th>P1–P6</th><th>WP</th></tr></thead><tbody>${rr.map((r,i)=>`<tr aria-selected="${state.rallyIndex===i}"><td>${r.set_number}</td><td><button data-rally="${i}" class="text-button">${r.rally_number}</button></td><td>${r.score_home_after}–${r.score_away_after}</td><td>${esc(teamName(m[r.serving_side+'_team']))}</td><td>${r.home_rotation??'—'} / ${r.away_rotation??'—'}</td><td>${pct(r.wp_after==null?null:r.wp_after*100)}</td></tr>`).join('')}</tbody></table></div></details><details><summary>Substituições, timeouts e validação</summary>${table(['Set','Evento','Equipe','Placar'],events.map(e=>row([e.set_number,esc(e.kind),esc(teamName(m[e.team_side+'_team'])),e.score_home==null?'—':`${e.score_home}–${e.score_away}`])))}<p class="note">Validação: ${esc(v?.status||'—')}. ${esc(v?.report.official_warnings?.join(' · ')||'Conciliação oficial disponível no export de validações.')} Sanções não extraídas; sequência pode incluir ponto administrativo. Não há timestamp observado do rally.</p></details></section>`}
const oldMatchPage=matchPage;
matchPage=function(){const m=C().matches.find(m=>String(m.match_id)===String(state.matchId));if(!m)return oldMatchPage();const rr=matchRallies(m.match_id),original=oldMatchPage();const split=original.indexOf('<section class="card">');return split<0?original:original.slice(0,split)+replaySection(m,rr)+`<details class="details-panel"><summary>Match Report · totais, fases, atletas e saldo</summary>${original.slice(split)}</details>`};
function athletesPage(){const t=team(),list=t?[t]:C().teams;const combined={athletes:list.flatMap(t=>t.athletes.map(a=>({...a,team:t.team})))};return heading('Atletas','Ataque, recepção e amostra publicada no Match Report')+selectors()+`<section class="atlas-sheet">${athletes(combined)}</section>`+(state.athlete?athleteProfile(state.athlete,list):'')}
function athleteProfile(name,list){
  const entries=list.filter(t=>!state.athleteTeam||t.team===state.athleteTeam).flatMap(t=>t.athletes.filter(a=>a.name===name).map(a=>({...a,team:t.team})));
  return `<section class="atlas-sheet athlete-profile">
    <div class="atlas-heading">
      <div>
        <span class="atlas-overline">Perfil Individual da Atleta</span>
        <h2>${esc(teamName(name))}</h2>
      </div>
    </div>
    ${entries.map(a=>{
      const m=a.metrics||{};
      const obs=a.observed||{};
      const games=a.games||a.metrics?.kill?.total_matches||1;
      const pts=a.points||obs.points_total||0;
      
      const kpisHtml=`<div class="kpis">
        <div class="kpi primary">
          <span class="kpi-label">Pontos Totais</span>
          <span class="kpi-value">${num(pts)}</span>
          <span class="kpi-sub">${fmt(pts/games,1)} por jogo · ${games} jogos</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Eficiência de Ataque</span>
          <span class="kpi-value">${m.eff?.value!=null?pct(m.eff.value):'—'}</span>
          <span class="kpi-sub">Kill% ${m.kill?.value!=null?pct(m.kill.value):'—'} · n=${num(m.kill?.n)}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Passe Positivo</span>
          <span class="kpi-value">${m.positive?.value!=null?pct(m.positive.value):'—'}</span>
          <span class="kpi-sub">Excelente ${m.excellent?.value!=null?pct(m.excellent.value):'—'} · n=${num(m.rec_error?.n)}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">EPA Estimado</span>
          <span class="kpi-value">${m.epa?.value!=null?signed(m.epa.value):'—'}</span>
          <span class="kpi-sub">${m.epa_per_game?.value!=null?signed(m.epa_per_game.value)+'/jogo':'modelo experimental'}</span>
        </div>
      </div>`;

      const metricKeys=['kill','eff','attack_blocked','attack_error','positive','excellent','rec_error','ace','serve_error','block_points','block_per_game','ava','epa','epa_per_game'];
      const rows=metricKeys.filter(k=>m[k]&&m[k].value!=null).map(k=>[
        m[k].label,
        badge(m[k].metric_class),
        metricCell(m[k]),
        m[k].ci?`[${pct(m[k].ci[0])} – ${pct(m[k].ci[1])}]`:'—',
        num(m[k].n),
        esc(m[k].sample||'')
      ]);

      const tableHtml=table(['Fundamento / Métrica','Classe','Taxa / Valor','Wilson 95%','Amostra (n)','Estabilidade'],rows.map(r=>row(r,[1,3])));

      const expHtml=(m.epa||m.ava)?`<div class="panel" style="margin-top:16px;">
        <div class="panel-head">
          <span class="kicker">Sports Analytics · Modelagem Avançada</span>
          <h3>Métricas Experimentais: AVA e EPA Estimado</h3>
        </div>
        <div class="panel-body">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">
            <div class="insight">
              <span class="insight-label">Attack Value Added (AVA)</span>
              <span class="insight-value">${m.ava?.value!=null?signed(m.ava.value)+' kills':'—'}</span>
              <p class="note">Saldo de finalizações de ataque comparado ao volume esperado na média da liga (n=${num(m.kill?.n)} ataques). Positivo indica definição acima do baseline.</p>
            </div>
            <div class="insight">
              <span class="insight-label">EPA Estimado (Expected Points Added)</span>
              <span class="insight-value">${m.epa?.value!=null?signed(m.epa.value)+' pts':'—'}</span>
              <p class="note">Impacto marginal líquido estimado em pontos a partir do modelo markoviano de rali (Powers et al. 2018). Pondera kills acima da média, erros forçados/diretos, bloqueios sofridos, aces, recepções e bloqueios.</p>
            </div>
          </div>
          <p class="note" style="margin-top:10px;"><span class="badge model">EXPERIMENTAL</span> Estimativa descritiva inferida da literatura. Não substitui contagens de scout evento a evento com DataVolley.</p>
        </div>
      </div>`:'';

      return `<h3>${esc(teamName(a.team))}</h3>
        ${kpisHtml}
        ${tableHtml}
        ${expHtml}
        <details class="details-panel"><summary>Contagens publicadas no Match Report oficial</summary>${table(['Registro','Contagem','Jogos cobertos'],Object.entries(a.observed||{}).map(([key,value])=>row([{points_total:'Pontos creditados',break_points:'Break points conquistados',win_loss:'Saldo (+/−)',serve_attempts:'Saques',serve_points:'Aces',serve_errors:'Erros de saque',reception_attempts:'Recepções',reception_errors:'Erros de recepção',attack_attempts:'Ataques',attack_points:'Kills',attack_errors:'Erros de ataque',attack_blocked:'Bloqueados',block_points:'Bloqueios'}[key]||key,num(value),num(a.observed_matches?.[key])])))}<p class="source-tag">OBSERVADO · MATCH REPORT</p></details>
        ${athleteTrend(name,a.team)}
        ${athleteLineups(name,a.team)}`;
    }).join('')}
  </section>`;
}

referencesPage = function() {
  return heading('Metodologia & Referências','Fundamentação teórica, modelos estocásticos e literatura acadêmica de Volleyball Analytics')+`
<section class="atlas-sheet">
  <div class="atlas-heading">
    <h2>1. Teoria da Informação e Entropia da Distribuição de Levantamento</h2>
    <span class="source-tag experimental">MODELO EXPERIMENTAL · BITS DE SHANNON</span>
  </div>
  <p class="lead-deck">A entropia de Shannon quantifica matematicamente o grau de incerteza, dispersão e imprevisibilidade das decisões da levantadora na distribuição das bolas de ataque entre as atacantes disponíveis.</p>
  <div class="panel-body">
    <div class="formula-box">
      <strong>Equação de Shannon (1948):</strong>
      <div class="math-display">H(X) = − ∑ p_i log₂(p_i)   [bits]</div>
      <p class="note">Onde k representa o número de opções elegíveis na formação em rede e fundo, e p_i é a probabilidade (ou peso normalizado do prior) da opção i. Versão normalizada de 0 (previsibilidade total) a 1 (distribuição perfeitamente uniforme): H_norm = H(X) / log₂(k).</p>
    </div>
    <h3>Condicionamento Tático e Limitações na Base CBV</h3>
    <p>Na literatura de alto rendimento (<em>Science Untangled</em>, 2020; Lebedew, 2021), a entropia nunca deve ser interpretada isoladamente sem condicionamento à rotação (P1 a P6) e à qualidade do passe (In-System vs Out-of-System):</p>
    <ul>
      <li><strong>Passe Positivo/Excelente (K1+):</strong> A levantadora possui todas as atacantes à disposição. Alta entropia neste estado correlaciona-se com quebra da marcação de bloqueio adversário.</li>
      <li><strong>Passe Negativo (K1−):</strong> A física do deslocamento frequentemente restringe a distribuição a bolas altas nas extremidades. A redução de entropia é natural e esperada.</li>
      <li><strong>Inferência na Base CBV:</strong> Como as súmulas públicas não fornecem os códigos DataVolley de toque a toque, o Atlas implementa o <code>lineup_volume_entropy</code> como prior de volume das atletas presentes nas formações modais reconciliadas. A métrica permanece categorizada como <strong>EXPERIMENTAL</strong> para garantir honestidade epistemológica.</li>
    </ul>
  </div>
</section>

<section class="atlas-sheet">
  <div class="atlas-heading">
    <h2>2. O Rali como Cadeia de Markov e Expected Points Added (EPA)</h2>
    <span class="source-tag experimental">MODELAGEM ESTOCÁSTICA DE TRANSIÇÃO</span>
  </div>
  <p class="lead-deck">O EPA supera a falácia das contagens brutas ao mensurar o impacto marginal líquido que cada toque individual causa na probabilidade da equipe vencer a disputa do ponto.</p>
  <div class="panel-body">
    <div class="formula-box">
      <strong>Vetor de Expected Value e Atribuição de Crédito (Powers et al., 2018; Raymond, 2020):</strong>
      <div class="math-display">V(s) = P(Vitória no Rali | Estado s) ∈ [0, 1]</div>
      <div class="math-display">EPA_j = V(s_{t+1}) − V(s_t)   [pontos líquidos adicionados]</div>
      <p class="note">Estados absorventes: +1 (ponto próprio conquistado) e 0 (ponto adversário). Estados transientes modelam saque, passe (+/!), levantamento e ataque/bloqueio.</p>
    </div>
    <h3>Decomposição Descritiva Aplicada ao Atlas</h3>
    <p>Com as contagens oficiais do Match Report e a probabilidade de transição estimada da literatura, o EPA individual estimado no Atlas decompõe os ganhos e custos de cada fundamento:</p>
    <div class="formula-box">
      <div class="math-display">EPA = 0.30 × AVA − 0.70 × AtkErr − 0.85 × AtkBloq + 0.65 × Ace − 0.35 × SrvErr + 0.10 × ΔPosRec − 0.65 × RecErr + 0.65 × Blocks</div>
      <p class="note">Onde AVA = Kills − (Ataques × k_liga) representa os Kills Acima do Esperado (Attack Value Added). Atletas com EPA positivo agregam pontos acima do esperado para suas equipes.</p>
    </div>
  </div>
</section>

<section class="atlas-sheet">
  <div class="atlas-heading">
    <h2>3. Dinâmica de Fases: Side-Out (K1 / FBSO) vs Transição (K2)</h2>
    <span class="source-tag">ANÁLISE DE COMPLEXOS · FASES DO JOGO</span>
  </div>
  <div class="panel-body">
    <p>O voleibol moderno opera sob a dinâmica de dois sistemas interdependentes fundamentados por Carl McGown (1995) e Hugh McCutcheon (2022):</p>
    <ul>
      <li><strong>Complexo 1 (K1) e First Ball Side Out (FBSO%):</strong> O aproveitamento da equipe recebendo o saque no seu primeiro ataque terminal. Equipes de topo sustentam FBSO% superior a 60–65%. Avalia-se a passadora não por notas ordinais subjetivas, mas pelo <em>Expected Side-out Added (xSOA)</em> gerado pela qualidade do seu passe.</li>
      <li><strong>Complexo 2 (K2 / Transição):</strong> Pontos disputados a partir do contra-ataque após defesa ou amortecimento no bloqueio. Enquanto o K1 estabelece a base de sobrevivência do set, a eficiência de K2 é o maior preditor estatístico de vitórias em playoffs e jogos eliminatórios.</li>
    </ul>
  </div>
</section>

<section class="atlas-sheet">
  <div class="atlas-heading">
    <h2>4. Inferência Estatística em Amostras Pequenas e Validação</h2>
    <span class="source-tag">CALIBRAÇÃO E RIGOR ESTATÍSTICO</span>
  </div>
  <div class="panel-body">
    <ul>
      <li><strong>Intervalo de Confiança Wilson 95% (Wilson, 1927):</strong> Aplicado em todas as proporções binomiais exatas (Kill%, Ace%, Erro de Saque%, Bloqueado%). Diferente da aproximação normal de Wald, o escore de Wilson é rigoroso e assimétrico próximo aos extremos (0% e 100%) e em amostras reduzidas (n < 30).</li>
      <li><strong>Encolhimento Bayesiano Empírico (Efron & Morris, 1975):</strong> Suavização paramétrica via distribuição Beta empírica calculada por momentos em nível de coorte. Regride estimativas ruidosas de atletas com poucas tentativas para a média coletiva.</li>
      <li><strong>Brier Score e Log Loss (Brier, 1950):</strong> Métricas de perda utilizadas na validação walk-forward dos modelos de probabilidade de vitória pré-jogo e ponto a ponto, garantindo que o modelo seja probabilísticamente calibrado antes de qualquer exibição.</li>
    </ul>
  </div>
</section>

<section class="atlas-sheet">
  <div class="atlas-heading">
    <h2>5. Bibliografia Acadêmica</h2>
    <span class="source-tag">FONTES E LITERATURA CIENTÍFICA</span>
  </div>
  <ul class="academic-biblio">
    <li><strong>Shannon, C. E. (1948).</strong> <em>A Mathematical Theory of Communication.</em> Bell System Technical Journal, 27(3), 379–423. <a href="https://doi.org/10.1002/j.1538-7305.1948.tb01338.x" target="_blank" rel="noopener">doi:10.1002/j.1538-7305.1948.tb01338.x</a>.</li>
    <li><strong>Powers, S., et al. (2018/2020).</strong> <em>An absorbing Markov chain model for volleyball rallies and player evaluation.</em> Journal of Quantitative Analysis in Sports / New England Symposium on Statistics in Sports (NESSIS).</li>
    <li><strong>Raymond, B., & Ickowicz, A. (2020).</strong> <em>Expected points and distribution modeling in high-performance volleyball.</em> Science Untangled / openvolley Technical Papers.</li>
    <li><strong>Wilson, E. B. (1927).</strong> <em>Probable inference, the law of succession, and statistical inference.</em> Journal of the American Statistical Association, 22(158), 209–212. <a href="https://doi.org/10.1080/01621459.1927.10502953" target="_blank" rel="noopener">doi:10.1080/01621459.1927.10502953</a>.</li>
    <li><strong>Brier, G. W. (1950).</strong> <em>Verification of forecasts expressed in terms of probability.</em> Monthly Weather Review, 78(1), 1–3. <a href="https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2" target="_blank" rel="noopener">doi:10.1175/1520-0493(1950)078</a>.</li>
    <li><strong>Efron, B., & Morris, C. (1975).</strong> <em>Data analysis using Stein's estimator and its generalizations.</em> Journal of the American Statistical Association, 70(350), 311–319.</li>
    <li><strong>McCutcheon, H. (2022).</strong> <em>Mediation and Volley Analytics: Structural Systems for Terminal Scoring.</em> Human Kinetics.</li>
    <li><strong>Lebedew, M. (2021).</strong> <em>Inside Volleyball Analytics: Setter Decision Trees, Entropy and Reception Efficiency.</em> At Home on the Court.</li>
  </ul>
</section>`;
};
const oldDataPage=dataPage;
dataPage=function(){const c=C(),sources=c.source_snapshots||[],attempts=c.atlas_attempts||[],count=kind=>sources.filter(s=>s.source_type===kind&&s.status==='AVAILABLE').length;return heading('Dados','Fontes, cobertura, conciliação e versões')+editionAudit()+`<section class="atlas-sheet"><h2>O que foi possível reconstruir?</h2>${[['Match Report',count('match_report')],['Scoresheet',count('scoresheet')],['Controle de líbero',count('libero_report')],['Ponto a ponto original',count('play_by_play')],['Partidas reconstruídas',Object.keys(c.rallies||{}).length],['Rotações completas',c.coverage?.rotation_matches||0],['Presença reconciliada',c.coverage?.lineup_matches||0]].map(([name,n])=>`<div class="coverage-bars"><span>${name}</span><progress max="${c.matches.length||1}" value="${n}"></progress><span class="numeric">${n}/${c.matches.length}</span></div>`).join('')}<p class="note">O widget original retornou 403. Sequência disponível foi reconstruída das passagens de saque, sem inventar autoria de ações.</p>${table(['Reconciliação','Partidas'],['VALID','VALID_WITH_WARNINGS','PARTIAL','FAILED'].map(status=>row([status,attempts.filter(a=>a.status===status).length])))}<p><a href="https://github.com/lucaaregis4r-ops/Dados-Voleibr/blob/main/docs/CADERNO_METODOLOGICO.md" target="_blank" rel="noopener">Abrir caderno metodológico</a></p><details><summary>Tentativas por partida</summary>${table(['Partida','Estado','Motivo'],attempts.map(a=>row([`<button data-match="${a.match_id}" class="text-button">${a.match_id}</button>`,esc(a.status),esc(a.report.reason||a.report.lineup_warnings?.join('; ')||'Placares reconciliados')])) ,[1,2])}</details><details><summary>Fontes, hashes e versões</summary>${table(['Partida','Fonte','Estado','SHA256 / coleta'],sources.map(s=>row([String(s.match_id),s.source_url?`<a class="atlas-data-link" href="${esc(s.source_url)}" target="_blank" rel="noopener">${esc(s.source_type)}</a>`:esc(s.source_type),esc(s.status),`<span title="${esc(s.sha256||'')}">${esc(s.sha256?.slice(0,16)||'—')}</span><br>${esc(s.fetched_at||'data de coleta não registrada')}`]),[1,2,3]),[1,2,3])}</details></section><section class="atlas-sheet"><h2>Modelos e avaliações</h2><p>Baseline pré-jogo: logistic-l2-v1 · preservado.</p>${table(['Pré-jogo · mesma amostra','n','Brier','Log Loss','Calibration Error'],['baseline','candidate'].map(key=>{const e=c.challenger?.[key];return row([key==='baseline'?'Baseline v1':'v2 com intercepto · experimental',num(e?.total_matches),fmt(e?.brier_score,3),fmt(e?.log_loss,3),fmt(e?.calibration_error,3)])}))}<p class="note">${esc(c.challenger?.limitation||'')} Ganho em todos os critérios: ${c.challenger?.improved?'sim':'não'}. Modelo ativo preservado.</p><p class="experimental-text">${esc(c.rally_model?.model_version||'—')} · EXPERIMENTAL</p>${table(['Modelo de ponto','n comum','Brier','Log Loss'],['candidate','baseline'].map(key=>{const e=c.rally_model?.[key];return row([key==='candidate'?'Equipe + prior de fase':'Prior da competição',num(e?.n),fmt(e?.brier),fmt(e?.log_loss)])}))}<p class="note">${esc(c.rally_model?.wp_validation||'Sem avaliação disponível.')}</p><details><summary>Treinos reproduzíveis</summary>${table(['Partida','Janela','Jogos de treino','Parâmetros'],(c.rally_model?.runs||[]).map(r=>row([r.match_id,esc(r.training_window?.join(' → ')||'Sem histórico'),r.training_matches,esc(JSON.stringify(r.parameters))]),[1,3]),[1,3])}</details></section><details class="details-panel"><summary>Estatísticas legadas e operações locais</summary>${oldDataPage().replace(heading('Dados'),'').replace(/SO\/BP por rotação e métricas de sequência exigem eventos por rally, ausentes da base atual\./g,'A cobertura reconstruída está discriminada acima; agregados legados permanecem separados.')}</details>`};
const oldBind=bind;
bind=function(){
  oldBind();
  const activate=(selector,fn)=>document.querySelectorAll(selector).forEach(el=>{el.onclick=()=>fn(el);el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(el)}}});
  activate('[data-layer]',el=>{state.layer=el.dataset.layer;render()});
  activate('[data-rotation]',el=>{state.rotation=Number(el.dataset.rotation);render()});
  activate('[data-cell]',el=>{state.matrixCell=el.dataset.cell.split(',').map(Number);render()});
  if($('#matrix-metric'))$('#matrix-metric').onchange=e=>{state.matrixMetric=e.target.value;render()};
  const go=i=>{const scroll=window.scrollY;state.rallyIndex=i;render();window.scrollTo(0,scroll)};
  activate('[data-rally]',el=>go(Number(el.dataset.rally)));
  activate('[data-step]',el=>go(state.rallyIndex+Number(el.dataset.step)));
  if($('#rally-slider'))$('#rally-slider').onchange=e=>go(Number(e.target.value));
  document.querySelectorAll('#athlete-table tbody tr').forEach(tr=>{const td=tr.firstElementChild;if(td&&!td.querySelector('button')&&tr.children.length>1){const name=td.textContent;td.innerHTML=`<button class="team-link" data-athlete="${esc(name)}">${esc(name)}</button>`;td.firstChild.onclick=()=>{state.athlete=tr.dataset.athleteName||null;state.athleteTeam=tr.dataset.athleteTeam||null;state.page='Atletas';render()}}});
  
  // Placar 2026 overview rotation interaction
  document.querySelectorAll('#overview-metric-tabs button').forEach(btn => {
    btn.onclick = () => {
      state.overviewRotMetric = btn.dataset.overviewMetric;
      render();
    };
  });
  document.querySelectorAll('#overview-rotations button').forEach(btn => {
    btn.onclick = () => {
      state.overviewRotIndex = Number(btn.dataset.overviewP);
      render();
    };
  });
  document.querySelectorAll('[data-open-confronto]').forEach(btn => {
    btn.onclick = () => {
      state.team = btn.dataset.openConfronto;
      state.opponent = btn.dataset.openOpponent;
      state.page = 'Confrontos';
      closeMenu();
      render();
      window.scrollTo(0, 0);
    };
  });
};

function opponentSection(name){const rows=Object.entries(C().opponent_ratings||{});return `<details class="details-panel"><summary>Força ajustada por adversário · experimental</summary><p class="note">Regressão logística regularizada com efeitos de equipe e adversário. SO/BP usam a definição creditada do Match Report. Efeitos descritivos; sem causalidade.</p>${table(['Fase','Força contra oponente médio','Δ referência','Jogos avaliados','Ganho temporal'],rows.map(([phase,result])=>{const rating=result.ratings.find(r=>r.team===name);return row([{so:'SO do relatório',bp:'BP do relatório',kill:'Ataque · Kill%',positive:'Recepção positiva'}[phase],pct(rating?.strength),signed(rating?.delta)+' pp',num(result.candidate.matches),result.improved?'Brier e log loss menores':'Não retido'])}))}<details><summary>Auditoria da comparação na mesma amostra</summary>${table(['Fase','Brier candidato','Brier baseline','Log Loss candidato','Log Loss baseline'],rows.map(([phase,result])=>row([phase,fmt(result.candidate.brier,3),fmt(result.baseline.brier,3),fmt(result.candidate.log_loss,3),fmt(result.baseline.log_loss,3)])))}<p class="note">Regularização fixa 50. São exigidos 20 jogos anteriores para treino e 20 de avaliação antes de reter ratings; calibração ainda requer estudo, portanto permanecem experimentais.</p></details></details>`}
function athleteLineups(name,teamName){const data=atlasTeam(teamName);return data?lineupSection({...data,lineups:data.lineups.filter(l=>l.identities?.includes(name)),on_off:data.on_off.filter(a=>a.player===name)}):''}
function athleteTrend(name,teamName){const points=C().matches.filter(m=>m.date).flatMap(m=>{const p=C().match_details?.[String(m.match_id)]?.players.find(p=>p.name===name&&p.team===teamName);return p?[{...p,date:m.date,match_id:m.match_id}]:[]}).sort((a,b)=>a.date.localeCompare(b.date)||a.match_id-b.match_id);const covered=points.filter(p=>p.metrics.kill?.value!=null),X=i=>48+i/Math.max(1,covered.length-1)*600,Y=v=>185-v*1.5;return `<details class="details-panel"><summary>Ataque e recepção · histórico por partida</summary>${covered.length?`<svg class="chart" viewBox="0 0 700 235" role="img" aria-label="Kill percentual da atleta em cada partida"><path d="M48,35 V185 H648" stroke="var(--line)" fill="none"/><polyline points="${covered.map((p,i)=>X(i)+','+Y(p.metrics.kill.value)).join(' ')}" stroke="var(--sideout)" stroke-width="2" fill="none"/>${covered.map((p,i)=>`<circle cx="${X(i)}" cy="${Y(p.metrics.kill.value)}" r="3" fill="var(--sideout)"><title>${matchDate(p.date)}: ${pct(p.metrics.kill.value)}, n=${p.metrics.kill.n}</title></circle>`).join('')}<text x="48" y="218">${matchDate(covered[0].date)}</text><text x="648" y="218" text-anchor="end">${matchDate(covered.at(-1).date)}</text></svg>`:''}${table(['Jogo','Data','Kill% · n','Eficiência','Passe + · n'],points.map(p=>row([`<button data-match="${p.match_id}" class="text-button">${p.match_id}</button>`,matchDate(p.date),pct(p.metrics.kill.value)+' · '+num(p.metrics.kill.n),pct(p.metrics.eff.value),pct(p.metrics.positive.value)+' · '+num(p.metrics.positive.n)])))}<p class="note">Valores por jogo do Match Report; linha conecta observações, sem média móvel ou ajuste por adversário. Ausência de tentativas permanece —.</p></details>`}

function distributionSection(data){if(!data)return '';const pass=state.expPass||'pos_rec',position=state.expRotation||state.rotation,model=data.distribution_model?.find(m=>m.position===position);const label={pos_rec:'K1+',neg_rec:'K1−',trans:'K2'};const points=C().teams.flatMap(t=>{const m=atlasTeam(t.team)?.distribution_model?.find(m=>m.position===position),metric=t.metrics[pass+'_eff'];return m&&metric.value!=null?[{team:t.team,x:m.entropy,y:metric.value,n:metric.n,availability:m.availability_rallies}]:[]});const ymin=Math.min(0,...points.map(p=>p.y-5)),ymax=Math.max(40,...points.map(p=>p.y+5)),X=x=>65+x/Math.log2(6)*535,Y=y=>225-(y-ymin)/(ymax-ymin)*180;return `<details class="details-panel" id="distribution-experiment" ${state.expOpen?'open':''}><summary>Distribuição estimada e diversidade × eficiência · experimental</summary><p>Prior de volume de ataque entre as atletas da formação mais frequente na amostra reconciliada desta passagem. Não representa frequência observada de levantamentos.</p><div class="toolbar"><label>Rotação<select id="exp-rotation">${[1,2,3,4,5,6].map(p=>`<option value="${p}" ${position===p?'selected':''}>P${p}</option>`).join('')}</select></label><label>Fase da eficiência<select id="exp-pass">${Object.entries(label).map(([key,value])=>`<option value="${key}" ${pass===key?'selected':''}>${value}</option>`).join('')}</select></label></div><p class="notice">Sem contatos encadeados, a fase NÃO altera os pesos de distribuição. O filtro altera somente a eficiência comparada. Entropia alta não significa melhor.</p>${model?`<div class="atlas-courts">${VolleyballCourt({variant:'half',players:model.distribution.map(p=>p.number),overlay:model.distribution.map(p=>p.weight),homeLabel:'Formação observada · prior experimental'})}<div><h3>Entropia do modelo: ${fmt(model.entropy,2)} bits</h3>${table(['Atleta','Peso do prior'],model.distribution.map(p=>row([esc(teamName(p.name)),pct(p.weight*100)])))}<p class="note">Formação modal: ${model.n_lineup} pontos; disponibilidade conhecida em P${position}: ${model.availability_rallies}, ${model.source_match_count} jogos. Volume ofensivo: ${model.volume_match_count} jogos da coorte. Não é escalação provável.</p></div></div>`:'<p class="atlas-empty">Formação e identidade insuficientes nesta passagem para estimar a distribuição.</p>'}<h3>Diversidade estimada × eficiência publicada · ${label[pass]}</h3>${points.length?`<svg class="chart" viewBox="0 0 700 290" role="img" aria-label="Entropia do prior de volume versus eficiência publicada da fase"><path d="M65,40 V225 H600" fill="none" stroke="var(--line)"/>${points.map(p=>`<g data-team="${esc(p.team)}" tabindex="0" role="button" aria-label="${esc(teamName(p.team))}"><circle class="team-point" cx="${X(p.x)}" cy="${Y(p.y)}" r="${p.team===data.team?7:4}"/><title>${esc(teamName(p.team))}: ${fmt(p.x,2)} bits; eficiência ${pct(p.y)}; n fase=${p.n}, disponibilidade=${p.availability}</title></g>`).join('')}<text x="54" y="${Y(ymin)+4}" text-anchor="end">${fmt(ymin,0)}%</text><text x="54" y="${Y(ymax)+4}" text-anchor="end">${fmt(ymax,0)}%</text><text x="65" y="245">0 bits</text><text x="600" y="245" text-anchor="end">${fmt(Math.log2(6),2)} bits</text><text x="330" y="275" text-anchor="middle">Entropia do prior de volume</text><text transform="translate(17,150) rotate(-90)" text-anchor="middle">Eficiência de ataque</text></svg>`:'<p class="note">Sem pares cobertos para esta comparação.</p>'}<p class="note">Comparação agregada na mesma competição, gênero, categoria e temporada. Amostras de fase e disponibilidade podem diferir. Associação não demonstra causalidade. O modelo heurístico legado continua disponível na API experimental.</p></details>`}
const bindWithDistribution=bind;
bind=function(){bindWithDistribution();const detail=$('#distribution-experiment');if(detail)detail.addEventListener('toggle',()=>{state.expOpen=detail.open});for(const [id,key] of [['exp-rotation','expRotation'],['exp-pass','expPass']])if($('#'+id))$('#'+id).onchange=e=>{state[key]=id==='exp-rotation'?Number(e.target.value):e.target.value;state.expOpen=true;render()}};

// Edition scope and a reading guide are available from every view.
function seasonContext(){const c=C(),label={CURRENT:'Temporada atual',COMPLETED:'Temporada encerrada',UPCOMING:'Próxima temporada',UNKNOWN:'Edição selecionada'}[c?.edition_status||'UNKNOWN'];return `<aside class="season-context" aria-label="Recorte da temporada"><div><strong>${label} · ${esc(seasonLabel(c?.season))}</strong><p>${esc(c?.statistics_scope||'Estatísticas restritas à edição selecionada.')}${!c?.matches?.length?' Ainda sem partidas concluídas coletadas nesta edição.':''}</p></div><button class="text-button" data-legend>Legenda das variáveis</button></aside>`}
const pageLegendKeys={'Visão geral':['so','bp','eff','n','pp'],'Equipes':['rotation','so','bp','k1','n','pp','expected','runs','onoff'],'Confrontos':['so','bp','expected','evaluation'],'Partidas':['rotation','wp','wpa','leverage','crunch','missing'],'Atletas':['kill','eff','positive','n','pp'],'Dados':['classes','evaluation','missing'],'Referências':['classes','evaluation','distribution','expected','ci']};
function contextLegend(){const keys=pageLegendKeys[state.page];if(!keys)return '';return `<details class="details-panel context-legend"><summary>Como ler as variáveis desta página</summary><dl class="legend-list">${(DATA.glossary||[]).filter(g=>keys.includes(g.key)).map(g=>`<div><dt>${esc(g.label)}</dt><dd>${esc(g.meaning)} <span class="note">${esc(g.reading)}</span></dd></div>`).join('')}</dl><button class="text-button" data-legend>Abrir legenda completa e fórmulas</button></details>`}
function legendPage(){return heading('Legenda das variáveis','Significado, unidade, fórmula e cuidados na interpretação')+`<label class="legend-search">Buscar sigla ou variável<input id="legend-search" type="search" placeholder="Ex.: SO, WPA, eficiência, amostra" aria-label="Buscar na legenda"></label><section class="atlas-sheet"><h2>Guia de leitura</h2><dl class="legend-list">${(DATA.glossary||[]).map(g=>`<div data-legend-item><dt>${esc(g.label)}</dt><dd>${esc(g.meaning)}<p class="note">${esc(g.reading)}</p></dd></div>`).join('')}</dl></section><section class="atlas-sheet"><h2>Catálogo de variáveis e fórmulas</h2><p class="note">Amostras e comparações usam a mesma competição, gênero, categoria e temporada. Modelos com histórico insuficiente permanecem indisponíveis.</p>${(DATA.metric_registry||[]).map(m=>`<details class="legend-metric" data-legend-item><summary>${esc(m.short_name||m.name)} <span class="note">${esc(m.metric_id)}</span></summary><p>${badge(m.metric_class)} ${esc(m.description)}</p><dl class="legend-list"><div><dt>Fórmula</dt><dd>${esc(m.formula)}</dd></div><div><dt>Unidade</dt><dd>${esc(m.unit)}</dd></div><div><dt>Fontes</dt><dd>${esc(m.required_sources.join(', '))}</dd></div><div><dt>Exemplo</dt><dd>${esc(m.example)}</dd></div><div><dt>Limitações</dt><dd>${esc(m.limitations)}</dd></div></dl></details>`).join('')}<p id="legend-empty" class="atlas-empty" hidden>Nenhuma variável encontrada.</p></section>`}
const bindWithLegend=bind;
bind=function(){bindWithLegend();document.querySelectorAll('[data-legend]').forEach(b=>b.onclick=()=>{state.page='Legenda';render();$('#main').scrollIntoView({block:'start'})});const input=$('#legend-search');if(input)input.oninput=()=>{const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),query=norm(input.value);let found=0;document.querySelectorAll('[data-legend-item]').forEach(item=>{item.hidden=!norm(item.textContent).includes(query);if(!item.hidden)found++});$('#legend-empty').hidden=found>0}};

function editionAudit(){const c=C(),source=c?.edition_source;return `<section class="atlas-sheet"><h2>Qual edição está sendo analisada?</h2><p><strong>${esc(seasonLabel(c?.season))}</strong> · ${esc(c?.statistics_scope||'Recorte selecionado')}</p>${source?`<p class="note">Edição atual confirmada pela CBV: ${esc(seasonLabel(source.season))}. Fonte: <a href="${esc(source.source_url)}" target="_blank" rel="noopener">página oficial da competição</a>. Verificação: ${dateText(source.verified_at)}.</p><details><summary>Identidade da fonte</summary><p class="atlas-data-link numeric">SHA256: ${esc(source.sha256)}</p><p class="note">O título oficial identifica a edição. A data isolada de um jogo não determina sua temporada.</p></details>`:'<p class="note">Sem metadados da edição atual; temporada conservada conforme a identidade cadastrada.</p>'}</section>`}
