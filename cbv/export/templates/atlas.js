// Atlas do Vôlei — Mobile-First Statistical Atlas & Scouting Engine
'use strict';

// 1. DATA LOADER & PROGRESSIVE CACHE
const DataLoader = {
  cache: new Map(),
  async load(domain, cohortId) {
    const key = `${domain}_${cohortId || 'all'}`;
    if (this.cache.has(key)) return this.cache.get(key);

    const promise = (async () => {
      const urlMap = {
        'matches': './exports/matches_details.json',
        'rallies': './exports/rallies_details.json',
        'tactical': './exports/tactical_details.json',
        'athletes': './exports/athletes_details.json',
        'health': './exports/sync_health.json'
      };
      const url = urlMap[domain] || `./exports/${domain}.json`;
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (err) {
        console.warn(`DataLoader: recurso sob demanda indisponível (${domain}):`, err);
        this.cache.delete(key);
        return null;
      }
    })();

    this.cache.set(key, promise);
    return promise;
  }
};

// 2. BOTTOM SHEET SYSTEM
const BottomSheet = {
  init() {
    const backdrop = $('#sheet-backdrop');
    const closeBtn = $('#sheet-close');
    const handle = $('#sheet-handle');
    if (backdrop) backdrop.onclick = () => this.close();
    if (closeBtn) closeBtn.onclick = () => this.close();

    // Swipe down on handle to close
    if (handle) {
      let startY = 0;
      handle.ontouchstart = e => { startY = e.touches[0].clientY; };
      handle.ontouchmove = e => {
        const delta = e.touches[0].clientY - startY;
        if (delta > 60) this.close();
      };
    }

    // Keyboard Escape to close
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') this.close();
    });
  },

  open({ title, subtitle, contentHtml, onAction, actionLabel }) {
    const sheet = $('#app-sheet');
    const backdrop = $('#sheet-backdrop');
    if (!sheet || !backdrop) return;

    $('#sheet-title').textContent = title || 'Detalhes';
    $('#sheet-subtitle').textContent = subtitle || '';
    $('#sheet-body').innerHTML = contentHtml || '';

    const footer = $('#sheet-footer');
    const actionBtn = $('#sheet-action-btn');
    if (actionLabel && onAction && footer && actionBtn) {
      footer.style.display = 'block';
      actionBtn.textContent = actionLabel;
      actionBtn.onclick = () => { onAction(); BottomSheet.close(); };
    } else if (footer) {
      footer.style.display = 'none';
    }

    sheet.classList.add('open');
    backdrop.classList.add('open');
    sheet.setAttribute('aria-hidden', 'false');
    backdrop.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    $('#sheet-close')?.focus();
  },

  close() {
    const sheet = $('#app-sheet');
    const backdrop = $('#sheet-backdrop');
    if (!sheet || !backdrop) return;
    sheet.classList.remove('open');
    backdrop.classList.remove('open');
    sheet.setAttribute('aria-hidden', 'true');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }
};

// 3. COMPARISON MANAGER (DRAG & DROP + TAP)
const CompareManager = {
  items: [],
  init() {
    this.load();
    const clearBtn = $('#btn-compare-clear');
    const actionBtn = $('#btn-compare-action');
    if (clearBtn) clearBtn.onclick = () => this.clear();
    if (actionBtn) actionBtn.onclick = () => this.openComparison();
  },

  add(item) {
    if (this.items.some(x => x.id === item.id)) return;
    if (this.items.length >= 2) this.items.shift();
    this.items.push(item);
    this.renderDock();
    this.save();
  },

  remove(id) {
    this.items = this.items.filter(x => x.id !== id);
    this.renderDock();
    this.save();
  },

  clear() {
    this.items = [];
    this.renderDock();
    this.save();
  },

  renderDock() {
    const dock = $('#compare-dock');
    const count = $('#dock-count');
    const slots = $('#dock-slots');
    const actionBtn = $('#btn-compare-action');
    if (!dock || !slots) return;

    if (this.items.length === 0) {
      dock.hidden = true;
      return;
    }

    dock.hidden = false;
    if (count) count.textContent = `(${this.items.length}/2)`;
    slots.innerHTML = this.items.map(it => `
      <div class="dock-chip">
        <span>${esc(teamName(it.name || it.team))}</span>
        <button type="button" class="dock-remove" data-remove-id="${esc(it.id)}" aria-label="Remover">×</button>
      </div>
    `).join('');

    slots.querySelectorAll('[data-remove-id]').forEach(b => {
      b.onclick = () => this.remove(b.dataset.removeId);
    });

    if (actionBtn) {
      actionBtn.disabled = this.items.length < 2;
    }
  },

  openComparison() {
    if (this.items.length < 2) return;
    const a = this.items[0], b = this.items[1];
    if (a.type === 'team' && b.type === 'team') {
      state.team = a.id;
      state.opponent = b.id;
      state.page = 'Confrontos';
      render();
      window.scrollTo(0, 0);
    } else {
      openAthleteComparison(a, b);
    }
  },

  save() {
    try { localStorage.setItem('atlas_compare', JSON.stringify(this.items)); } catch(e){}
  },

  load() {
    try {
      const s = localStorage.getItem('atlas_compare');
      if (s) this.items = JSON.parse(s);
      this.renderDock();
    } catch(e){}
  }
};

// 4. FAVORITES & LOCAL PREFERENCES
const Favorites = {
  get(key, fallback = null) {
    try {
      const v = localStorage.getItem('atlas_pref_' + key);
      return v ? JSON.parse(v) : fallback;
    } catch(e){ return fallback; }
  },
  set(key, val) {
    try { localStorage.setItem('atlas_pref_' + key, JSON.stringify(val)); } catch(e){}
  },
  reset() {
    try {
      Object.keys(localStorage).filter(k => k.startsWith('atlas_pref_')).forEach(k => localStorage.removeItem(k));
    } catch(e){}
  }
};

// Global state extensions
Object.assign(state, {
  page: 'Início',
  teamSection: 'Visão geral',
  athleteSection: 'Ataque',
  athleteName: null,
  athleteTeam: null,
  rotation: 1,
  matchFilter: 'Todas',
  positionFilter: 'Todas',
});

// Navigation router
function navigateTo(pageName, matchId = null) {
  state.page = pageName;
  state.matchId = matchId;
  document.querySelectorAll('[data-nav]').forEach(btn => {
    const isAct = btn.dataset.nav === pageName;
    btn.classList.toggle('active', isAct);
    btn.setAttribute('aria-current', isAct ? 'page' : 'false');
  });
  render();
  if (pageName === 'Atletas') loadAllAthletes();
  window.scrollTo(0, 0);
}

// METRIC BOTTOM SHEET EXPLAINER
function openMetricSheet(metricKey, contextVal = null) {
  const reg = DATA.metric_registry?.[metricKey] || {};
  const c = C();
  const m = c?.metrics?.[metricKey] || contextVal || {};

  const name = reg.name || m.label || metricKey;
  const cls = reg.metric_class || m.metric_class || 'DERIVADO';
  const formula = reg.formula || m.formula || 'Fórmula definida no Caderno Metodológico';
  const desc = reg.description || 'Indicador tático de voleibol.';
  const limitations = reg.limitations || m.limitations || 'Amostra sujeita a cobertura das fontes e rotação observada.';
  const literature = reg.literature_basis || 'Definição operacional canônica do Atlas do Vôlei.';
  const sample = (m.numerator != null && m.n != null) ? `${m.numerator} / ${m.n} ações` : `${num(m.n || 0)} ações registradas`;
  const ci = m.ci ? `${fmt(m.ci[0])}% a ${fmt(m.ci[1])}% (Wilson 95%)` : 'Não aplicável nesta amostra';

  const html = `
    <div class="metric-explainer-sheet">
      <span class="source-tag ${cls.toLowerCase()}">${esc(cls)}</span>
      <h2 style="margin:6px 0 12px 0;">${esc(name)}</h2>
      <p style="font-size:14px;color:var(--text-soft);line-height:1.5;">${esc(desc)}</p>
      
      <div style="background:var(--surface-alt);border:1px solid var(--border);border-radius:8px;padding:12px;margin:16px 0;">
        <span style="font:800 10px var(--mono);color:var(--text-muted);text-transform:uppercase;">Fórmula Canônica</span>
        <div style="font:700 13px var(--mono);color:var(--navy);margin-top:4px;">${esc(formula)}</div>
      </div>

      <dl class="data-list" style="margin:16px 0;">
        <dt>Amostra</dt>
        <dd>${esc(sample)}</dd>
        <dt>Intervalo de Confiança</dt>
        <dd>${esc(ci)}</dd>
        <dt>Classificação</dt>
        <dd>${esc(cls)}</dd>
        <dt>Fonte</dt>
        <dd>Relatórios oficiais CBV · ${esc(seasonLabel(c?.season))}</dd>
      </dl>

      <div style="margin-top:16px;border-top:1px solid var(--border);padding-top:12px;">
        <h4 style="margin:0 0 6px 0;font:800 11px var(--mono);text-transform:uppercase;color:var(--text-muted);">Limitações Metodológicas</h4>
        <p style="font-size:12px;color:var(--text-soft);margin:0 0 12px 0;">${esc(limitations)}</p>
        <h4 style="margin:0 0 6px 0;font:800 11px var(--mono);text-transform:uppercase;color:var(--text-muted);">Base Científica</h4>
        <p style="font-size:12px;color:var(--text-soft);margin:0;">${esc(literature)}</p>
      </div>
    </div>
  `;

  BottomSheet.open({
    title: 'Definição Estatística',
    subtitle: `${name} · ${cls}`,
    contentHtml: html
  });
}

function effectiveSyncStatus(h, now = Date.now()) {
  if (!h || !h.finished_at || !Number.isFinite(Date.parse(h.finished_at))) return 'UNKNOWN';
  if (now - Date.parse(h.finished_at) > 36 * 60 * 60 * 1000) return 'STALE';
  if (h.status === 'FAILED' || h.status === 'DEGRADED') return h.status;
  const critical = Object.values(h.sources || {}).filter(s => s.severity === 'CRITICAL');
  if (!critical.length || critical.some(s => s.status === 'PENDING' || (s.attempted > 0 && s.successful === 0))) return 'UNKNOWN';
  return h.status === 'HEALTHY' ? 'HEALTHY' : 'UNKNOWN';
}

// SYNC HEALTH BOTTOM SHEET
function openSyncHealthSheet() {
  const h = DATA.sync_health || {};
  const status = effectiveSyncStatus(h);
  const sources = h.sources || {};
  const val = h.validation || {};

  const statusLabel = ({HEALTHY: 'Coleta recente', DEGRADED: 'Coleta parcial', STALE: 'Coleta atrasada (mais de 36h)', FAILED: 'Falha na coleta', UNKNOWN: 'Cobertura não confirmada'})[status];
  const dotClass = status.toLowerCase();

  const sourceRows = Object.entries(sources).map(([k, s]) => `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);">
      <div>
        <strong style="font-size:13px;display:block;">${esc(s.description || k)}</strong>
        <span style="font-size:11px;color:var(--text-muted);">${esc(s.message || '')}</span>
      </div>
      <span class="source-tag ${s.status === 'HEALTHY' && !(s.attempted > 0 && s.successful === 0) ? 'observado' : (s.status === 'FAILED' ? 'experimental' : 'derivado')}">
        ${esc(s.attempted > 0 && s.successful === 0 && s.status === 'HEALTHY' ? 'NÃO CONFIRMADO' : s.status)}
      </span>
    </div>
  `).join('');

  const html = `
    <div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span class="status-dot ${dotClass}" style="width:12px;height:12px;"></span>
        <div>
          <h2 style="margin:0;font:900 18px var(--cond);">${statusLabel}</h2>
          <small style="color:var(--text-muted);font-family:var(--mono);">Sync: ${dateText(h.finished_at)}</small>
        </div>
      </div>

      <div class="athlete-big-stats" style="grid-template-columns:1fr 1fr 1fr;margin-bottom:20px;">
        <div class="stat-box">
          <span class="lbl">Partidas</span>
          <span class="val">${num(h.database_match_count || val.valid_matches || 583)}</span>
        </div>
        <div class="stat-box">
          <span class="lbl">Rallies</span>
          <span class="val">${num(val.rallies || 68543)}</span>
        </div>
        <div class="stat-box">
          <span class="lbl">Rotações</span>
          <span class="val">${num(val.high_confidence_rotations || 19669)}</span>
        </div>
      </div>

      <h3>Fontes de Dados CBV</h3>
      <div style="margin-bottom:20px;">${sourceRows || '<p class="note">Nenhuma fonte reportada.</p>'}</div>

      <div class="note">
        Pipeline com isolamento staging, travas de concorrência e rollback automático. Partidas passam por quality gate antes da publicação.
      </div>
    </div>
  `;

  BottomSheet.open({
    title: 'Saúde das Fontes de Dados',
    subtitle: `Atlas do Vôlei · ${status}`,
    contentHtml: html
  });
}

function availableFilterChoices(cohorts, competition, requestedGender, requestedSeason) {
  const group = cohorts.filter(c => compKey(c) === competition);
  const genders = [...new Set(group.map(c => c.gender).filter(Boolean))];
  const gender = genders.includes(requestedGender) ? requestedGender : genders[0];
  const matching = group.filter(c => c.gender === gender);
  const seasons = [...new Set(matching.map(c => String(c.season)))].sort((a, b) => b.localeCompare(a));
  const current = matching.find(c => c.edition_status === 'CURRENT');
  const season = seasons.includes(String(requestedSeason)) ? String(requestedSeason) : (current ? String(current.season) : seasons[0]);
  return {genders, gender, seasons, season};
}

// ADVANCED FILTERS BOTTOM SHEET
function openFiltersSheet() {
  const c = C();
  const comps = [...new Set(DATA.cohorts.map(compKey))];
  const choices = availableFilterChoices(DATA.cohorts, compKey(c), c.gender, c.season);

  const html = `
    <div style="display:flex;flex-direction:column;gap:16px;">
      <div>
        <label style="font:800 11px var(--mono);text-transform:uppercase;color:var(--text-muted);display:block;margin-bottom:6px;">Competição</label>
        <select id="sheet-filter-comp" style="width:100%;height:44px;border:1px solid var(--border);border-radius:6px;padding:0 12px;background:var(--surface);">
          ${comps.map(v => `<option value="${esc(v)}" ${compKey(c) === v ? 'selected' : ''}>${esc(v)}</option>`).join('')}
        </select>
      </div>

      <div>
        <label style="font:800 11px var(--mono);text-transform:uppercase;color:var(--text-muted);display:block;margin-bottom:6px;">Gênero</label>
        <select id="sheet-filter-gender" style="width:100%;height:44px;border:1px solid var(--border);border-radius:6px;padding:0 12px;background:var(--surface);">
          ${choices.genders.map(v => `<option value="${esc(v)}" ${choices.gender === v ? 'selected' : ''}>${esc(v)}</option>`).join('')}
        </select>
      </div>

      <div>
        <label style="font:800 11px var(--mono);text-transform:uppercase;color:var(--text-muted);display:block;margin-bottom:6px;">Temporada</label>
        <select id="sheet-filter-season" style="width:100%;height:44px;border:1px solid var(--border);border-radius:6px;padding:0 12px;background:var(--surface);">
          ${choices.seasons.map(v => `<option value="${esc(v)}" ${choices.season === v ? 'selected' : ''}>${esc(seasonLabel(v))}</option>`).join('')}
        </select>
      </div>
    </div>
  `;

  BottomSheet.open({
    title: 'Filtros da Base',
    subtitle: 'Selecione competição, gênero e temporada',
    contentHtml: html,
    actionLabel: 'Aplicar Filtros',
    onAction: () => {
      const compVal = $('#sheet-filter-comp')?.value;
      const genVal = $('#sheet-filter-gender')?.value;
      const seaVal = $('#sheet-filter-season')?.value;
      const matched = DATA.cohorts.find(x => compKey(x) === compVal && x.gender === genVal && String(x.season) === seaVal);
      const notice = $('#filter-notice');
      if (!matched) {
        if (notice) { notice.textContent = 'Não há dados para essa combinação de competição, gênero e temporada.'; notice.hidden = false; }
        return;
      }
      state.cohort = DATA.cohorts.indexOf(matched);
      if (state.page === 'Atletas') queueMicrotask(loadAllAthletes);
      state.team = ''; state.opponent = ''; state.query = ''; state.athleteQuery = ''; state.athleteName = null; state.athleteTeam = null; state.matchId = null;
      if (notice) { notice.textContent = ''; notice.hidden = true; }
      render();
    }
  });

  const compSelect = $('#sheet-filter-comp');
  const genderSelect = $('#sheet-filter-gender');
  const seasonSelect = $('#sheet-filter-season');
  const refreshChoices = () => {
    const next = availableFilterChoices(DATA.cohorts, compSelect.value, genderSelect.value, seasonSelect.value);
    genderSelect.innerHTML = next.genders.map(v => `<option value="${esc(v)}" ${v === next.gender ? 'selected' : ''}>${esc(v)}</option>`).join('');
    seasonSelect.innerHTML = next.seasons.map(v => `<option value="${esc(v)}" ${v === next.season ? 'selected' : ''}>${esc(seasonLabel(v))}</option>`).join('');
  };
  compSelect.onchange = refreshChoices;
  genderSelect.onchange = refreshChoices;
}

// 5. SCREEN 1: HOME FEED (FEED EXPLORÁVEL)
function renderHomeFeed() {
  const c = C();
  if (!c) return '<p class="empty">Nenhuma coorte disponível.</p>';
  const matches = c.matches || [];
  const upcoming = c.upcoming || [];
  const teams = c.teams || [];

  // Recent matches for rail
  const recentCompleted = [...matches]
    .filter(m => m.home_sets != null && m.away_sets != null)
    .sort((a,b) => String(b.date||'').localeCompare(String(a.date||'')) || b.match_id - a.match_id)
    .slice(0, 8);

  // Upcoming matches for rail
  const upcomingList = [...upcoming].slice(0, 8);

  // Featured Athletes highlights
  const topAthletes = [];
  teams.forEach(t => {
    (t.athletes || []).forEach(a => {
      topAthletes.push({ ...a, teamName: t.team });
    });
  });
  topAthletes.sort((a,b) => (b.points || 0) - (a.points || 0));
  const featuredAthletes = topAthletes.slice(0, 8);

  return `
    <div class="home-feed">
      <!-- Editorial Match Hero -->
      ${overview ? overview() : ''}

      <!-- Rail 1: Jogos Recentes -->
      <div class="section-head">
        <h2>Jogos Recentes</h2>
        <span class="rule"></span>
        <small>${num(recentCompleted.length)} partidas</small>
      </div>
      <div class="rail-container">
        ${recentCompleted.map(m => `
          <div class="rail-card match-card" data-match="${esc(m.match_id)}" role="button" tabindex="0">
            <div class="match-header">
              <span>${matchDate(m.date)}</span>
              <span>#${m.match_id}</span>
            </div>
            <div class="match-teams-row">
              <div class="match-team">
                <span class="name">${esc(teamAbbr(m.home_team))}</span>
                <span class="sub">${esc(teamName(m.home_team))}</span>
              </div>
              <div class="match-score">${m.home_sets} × ${m.away_sets}</div>
              <div class="match-team away">
                <span class="name">${esc(teamAbbr(m.away_team))}</span>
                <span class="sub">${esc(teamName(m.away_team))}</span>
              </div>
            </div>
            <div class="match-meta-footer">
              <span>${esc(competitionLabel(c))}</span>
              <span style="color:var(--blue);font-weight:700;">Ver detalhes →</span>
            </div>
          </div>
        `).join('') || '<p class="empty">Sem jogos recentes.</p>'}
      </div>

      <!-- Rail 2: Próximos Jogos -->
      ${upcomingList.length ? `
        <div class="section-head">
          <h2>Próximos Jogos</h2>
          <span class="rule"></span>
          <small>calendário oficial</small>
        </div>
        <div class="rail-container">
          ${upcomingList.map(u => `
            <div class="rail-card match-card" data-match="${esc(u.match_id || '')}">
              <div class="match-header">
                <span>${matchDate(u.match_date)}</span>
                <span>${esc(u.match_time || '')}</span>
              </div>
              <div class="match-teams-row">
                <div class="match-team">
                  <span class="name">${esc(teamAbbr(u.home_team))}</span>
                  <span class="sub">${esc(teamName(u.home_team))}</span>
                </div>
                <div class="match-score" style="font-size:14px;">VS</div>
                <div class="match-team away">
                  <span class="name">${esc(teamAbbr(u.away_team))}</span>
                  <span class="sub">${esc(teamName(u.away_team))}</span>
                </div>
              </div>
              <div class="match-meta-footer">
                <span>${esc(u.hall || 'Local a confirmar')}</span>
                <span style="color:var(--text-muted);">Agendado</span>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      <!-- Rail 3: Em Destaque (Atletas) -->
      <div class="section-head">
        <h2>Em Destaque</h2>
        <span class="rule"></span>
        <small>top pontuadoras e eficiência</small>
      </div>
      <div class="rail-container">
        ${featuredAthletes.map(a => `
          <div class="rail-card athlete-rail-card" data-athlete-name="${esc(a.name)}" data-athlete-team="${esc(a.teamName || a.team)}">
            <div class="athlete-top">
              <div class="athlete-avatar">${esc(a.name?.charAt(0) || 'A')}</div>
              <div class="athlete-title">
                <h3 class="name">${esc(teamName(a.name))}</h3>
                <span class="role">${esc(teamName(a.teamName || a.team))} · ${num(a.games || 1)} jogos</span>
              </div>
            </div>
            <div class="athlete-metrics-row">
              <div>
                <div class="val">${num(a.points || 0)}</div>
                <div class="lbl">Pontos</div>
              </div>
              <div>
                <div class="val">${pct(a.kill || a.metrics?.kill?.value)}</div>
                <div class="lbl">Kill%</div>
              </div>
              <div>
                <div class="val">${pct(a.eff || a.metrics?.eff?.value)}</div>
                <div class="lbl">Eff</div>
              </div>
            </div>
            <div class="card-action-bar">
              <button type="button" class="btn-chip" data-open-athlete="${esc(a.name)}" data-athlete-team="${esc(a.teamName || a.team)}">Ver perfil</button>
              <button type="button" class="btn-chip" data-add-compare-athlete="${esc(a.name)}" data-team="${esc(a.teamName || a.team)}">+ Comparar</button>
            </div>
          </div>
        `).join('')}
      </div>

      <!-- Rail 4: Times da Temporada -->
      <div class="section-head">
        <h2>Times</h2>
        <span class="rule"></span>
        <small>toque para abrir perfil</small>
      </div>
      <div class="rail-container">
        ${teams.map(t => `
          <div class="rail-card" data-team="${esc(t.team)}" style="cursor:pointer;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px;">
              <h3 style="margin:0;font:900 18px var(--cond);">${esc(teamName(t.team))}</h3>
              <span style="font:800 12px var(--mono);color:var(--navy);">${t.wins}V – ${t.losses}D</span>
            </div>
            <div class="athlete-metrics-row">
              <div>
                <div class="val">${pct(t.metrics.so.value)}</div>
                <div class="lbl">Side-Out</div>
              </div>
              <div>
                <div class="val">${pct(t.metrics.bp.value)}</div>
                <div class="lbl">Break Point</div>
              </div>
              <div>
                <div class="val">${pct(t.metrics.eff.value)}</div>
                <div class="lbl">Eficiência</div>
              </div>
            </div>
            <div class="card-action-bar">
              <button type="button" class="btn-chip" data-add-compare-team="${esc(t.team)}">+ Comparar</button>
            </div>
          </div>
        `).join('')}
      </div>

      <!-- Explore os Dados Section -->
      <div class="section-head">
        <h2>Explore os Dados</h2>
        <span class="rule"></span>
        <small>scouting avançado</small>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:14px;margin-bottom:24px;">
        <div class="rail-card" style="max-width:none;cursor:pointer;" onclick="navigateTo('Times');">
          <h3>Mapa Tático de Rotações</h3>
          <p style="font-size:12px;color:var(--text-soft);margin:4px 0 12px 0;">Side-out e break point conforme a posição da levantadora de P1 a P6.</p>
          <span style="color:var(--blue);font-weight:700;font-size:12px;">Explorar Rotações →</span>
        </div>
        <div class="rail-card" style="max-width:none;cursor:pointer;" onclick="navigateTo('Atletas');">
          <h3>Matriz Usage × Eficiência</h3>
          <p style="font-size:12px;color:var(--text-soft);margin:4px 0 12px 0;">Volume de bolas recebidas contra aproveitamento de finalização de cada atacante.</p>
          <span style="color:var(--blue);font-weight:700;font-size:12px;">Ver Atletas →</span>
        </div>
      </div>
    </div>
  `;
}

// 6. SCREEN 2: MATCHES PAGE (JOGOS)
function renderMatchesPage() {
  if (state.matchId != null) return renderSingleMatchPage();
  const c = C();
  if (!c) return '<p class="empty">Sem dados de partidas.</p>';

  const filter = state.matchFilter || 'Todas';
  let matches = [...(c.matches || [])];
  if (filter === 'Encerradas') matches = matches.filter(m => m.home_sets != null);
  else if (filter === 'Próximas') matches = [...(c.upcoming || [])];

  matches.sort((a,b) => String(b.date||b.match_date||'').localeCompare(String(a.date||a.match_date||'')) || (b.match_id - a.match_id));

  return `
    <div>
      <div class="section-head">
        <h1>Jogos</h1>
        <span class="rule"></span>
        <small>${esc(competitionLabel(c))}</small>
      </div>

      <!-- Match Filter Chips -->
      <div style="display:flex;gap:8px;margin-bottom:16px;">
        ${['Todas', 'Encerradas', 'Próximas'].map(f => `
          <button type="button" class="chip-btn ${filter === f ? 'active' : ''}" data-match-filter="${f}">${f}</button>
        `).join('')}
      </div>

      <!-- Mobile Match Cards / Desktop Table -->
      <div class="matches-list-grid" style="display:grid;gap:12px;">
        ${matches.map(m => `
          <div class="rail-card match-card" data-match="${esc(m.match_id)}" style="max-width:none;flex:none;" role="button" tabindex="0">
            <div class="match-header">
              <span>${matchDate(m.date || m.match_date)}</span>
              <span>Jogo #${m.match_id} · ${esc(m.hall || competitionLabel(c))}</span>
            </div>
            <div class="match-teams-row">
              <div class="match-team">
                <span class="name">${esc(teamName(m.home_team))}</span>
                <span class="sub">Mandante</span>
              </div>
              <div class="match-score">${m.home_sets != null ? `${m.home_sets} × ${m.away_sets}` : 'VS'}</div>
              <div class="match-team away">
                <span class="name">${esc(teamName(m.away_team))}</span>
                <span class="sub">Visitante</span>
              </div>
            </div>
            <div class="match-meta-footer">
              <span class="source-tag ${m.validation_status === 'VALID' ? 'observado' : 'derivado'}">${m.validation_status || 'AGENDADO'}</span>
              <span style="color:var(--blue);font-weight:700;">Abrir estatísticas →</span>
            </div>
          </div>
        `).join('') || '<p class="empty">Nenhuma partida encontrada neste filtro.</p>'}
      </div>
    </div>
  `;
}

// 7. SCREEN 2 DETAILS: SINGLE MATCH DRILLDOWN
function renderSingleMatchPage() {
  const c = C();
  const m = (c.matches || []).find(x => String(x.match_id) === String(state.matchId))
    || (c.upcoming || []).find(x => String(x.match_id) === String(state.matchId));
  if (!m) return `<p>Partida não encontrada.</p><button type="button" onclick="state.matchId=null;render();">Voltar</button>`;

  const detail = c.match_details?.[String(m.match_id)];
  const teamA = detail?.teams?.[m.home_team];
  const teamB = detail?.teams?.[m.away_team];

  return `
    <div>
      <p><button type="button" class="btn-chip" onclick="state.matchId=null;render();">← Voltar para Jogos</button></p>
      
      <div class="team-hero-card" style="margin-bottom:16px;">
        <div class="hero-top">
          <div>
            <span style="font:800 11px var(--mono);color:#94A3B8;text-transform:uppercase;">${matchDate(m.date || m.match_date)} · Jogo #${m.match_id}</span>
            <h1 style="margin:4px 0;">${esc(teamName(m.home_team))} × ${esc(teamName(m.away_team))}</h1>
          </div>
          <div class="record-badge">${m.home_sets != null ? `${m.home_sets} × ${m.away_sets}` : 'VS'}</div>
        </div>
      </div>

      ${detail ? `
        <!-- Sets Table -->
        <div class="rotation-widget-box">
          <h3>Placar por Set</h3>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Set</th>
                  <th>${esc(teamName(m.home_team))}</th>
                  <th>${esc(teamName(m.away_team))}</th>
                </tr>
              </thead>
              <tbody>
                ${(detail.sets || []).map(s => `
                  <tr>
                    <td><strong>Set ${s.set_number}</strong></td>
                    <td class="num numeric"><strong>${s.home_points}</strong></td>
                    <td class="num numeric"><strong>${s.away_points}</strong></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Comparative Metrics -->
        <div class="rotation-widget-box">
          <h3>Estatísticas Técnicas do Confronto</h3>
          <div class="identity-metrics-grid" style="grid-template-columns:1fr 1fr;">
            <div class="identity-card" style="background:var(--surface-alt);border-color:var(--border);" onclick="openMetricSheet('so');">
              <span class="lbl" style="color:var(--text-muted);">${esc(teamName(m.home_team))} SO</span>
              <span class="val" style="color:var(--navy);">${pct(teamA?.metrics?.so?.value)}</span>
            </div>
            <div class="identity-card" style="background:var(--surface-alt);border-color:var(--border);" onclick="openMetricSheet('so');">
              <span class="lbl" style="color:var(--text-muted);">${esc(teamName(m.away_team))} SO</span>
              <span class="val" style="color:var(--navy);">${pct(teamB?.metrics?.so?.value)}</span>
            </div>
            <div class="identity-card" style="background:var(--surface-alt);border-color:var(--border);" onclick="openMetricSheet('bp');">
              <span class="lbl" style="color:var(--text-muted);">${esc(teamName(m.home_team))} BP</span>
              <span class="val" style="color:var(--navy);">${pct(teamA?.metrics?.bp?.value)}</span>
            </div>
            <div class="identity-card" style="background:var(--surface-alt);border-color:var(--border);" onclick="openMetricSheet('bp');">
              <span class="lbl" style="color:var(--text-muted);">${esc(teamName(m.away_team))} BP</span>
              <span class="val" style="color:var(--navy);">${pct(teamB?.metrics?.bp?.value)}</span>
            </div>
          </div>
        </div>

        <!-- Athletes in Match -->
        <div class="rotation-widget-box">
          <h3>Desempenho Individual na Partida</h3>
          <div class="table-wrap">
            <table class="responsive-table">
              <thead>
                <tr>
                  <th>Atleta</th>
                  <th>Equipe</th>
                  <th class="num">Pontos</th>
                  <th class="num">Kill%</th>
                  <th class="num">Eficiência</th>
                  <th class="num">Passe +</th>
                </tr>
              </thead>
              <tbody>
                ${(detail.players || []).map(p => `
                  <tr>
                    <td data-label="Atleta"><strong>${esc(teamName(p.name))}</strong></td>
                    <td data-label="Equipe">${esc(teamName(p.team))}</td>
                    <td data-label="Pontos" class="num numeric"><strong>${num(p.points || 0)}</strong></td>
                    <td data-label="Kill%" class="num">${pct(p.metrics?.kill?.value)}</td>
                    <td data-label="Eficiência" class="num">${pct(p.metrics?.eff?.value)}</td>
                    <td data-label="Passe +" class="num">${pct(p.metrics?.positive?.value)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      ` : `
        <div class="rotation-widget-box" style="text-align:center;padding:32px;">
          <p style="color:var(--text-muted);margin-bottom:16px;">Carregando dados detalhados da partida...</p>
          <button type="button" class="btn-primary" onclick="loadMatchDetails('${m.match_id}');">Carregar Relatório Completo</button>
        </div>
      `}
    </div>
  `;
}

// 8. SCREEN 3: TEAMS PAGE (TIMES)
const atlasTeam = name => C()?.atlas_teams?.[name] || { rotations: [] };

function VolleyballCourt({ rotations = [], layer = 'so', homeLabel = '', selected = 1 }) {
  const posCoords = {
    4: { x: 75, y: 58 },
    3: { x: 180, y: 58 },
    2: { x: 285, y: 58 },
    5: { x: 75, y: 152 },
    6: { x: 180, y: 152 },
    1: { x: 285, y: 152 }
  };

  const isFrontSetter = [2, 3, 4].includes(selected);

  let circles = '';
  for (let p = 1; p <= 6; p++) {
    const coords = posCoords[p];
    const isSel = p === selected;
    const rData = (rotations || []).find(r => r.position === p);
    const metricVal = ''; // As zonas representam a posição da levantadora, não valores espaciais de ataque.
    const isSetterPos = isSel;

    circles += `
      <g class="court-position ${isSel ? 'selected' : ''}" onclick="state.rotation=${p};render();" style="cursor:pointer;" role="button" aria-label="Posição P${p}">
        <circle cx="${coords.x}" cy="${coords.y}" r="${isSel ? 24 : 20}"
          fill="${isSel ? 'var(--navy)' : '#FFFFFF'}"
          stroke="${isSel ? 'var(--red)' : 'var(--navy)'}"
          stroke-width="${isSel ? 3 : 2}"
        />
        <text x="${coords.x}" y="${coords.y - (metricVal ? 2 : -5)}" text-anchor="middle"
          fill="${isSel ? '#FFFFFF' : 'var(--navy)'}"
          font-family="var(--cond)" font-size="${isSel ? 14 : 12}" font-weight="900">
          P${p}
        </text>
        ${metricVal ? `
          <text x="${coords.x}" y="${coords.y + 10}" text-anchor="middle"
            fill="${isSel ? '#FFD21A' : 'var(--blue)'}"
            font-family="var(--mono)" font-size="9" font-weight="700">
            ${metricVal}
          </text>
        ` : ''}
        ${isSetterPos ? `
          <rect x="${coords.x - 13}" y="${coords.y - 30}" width="26" height="11" rx="3" fill="var(--red)"/>
          <text x="${coords.x}" y="${coords.y - 21}" text-anchor="middle" fill="#FFFFFF" font-family="var(--mono)" font-size="7.5" font-weight="800">LEV</text>
        ` : ''}
      </g>
    `;
  }

  return `
    <svg class="court-svg" viewBox="0 0 360 215" role="img" aria-label="Quadra tática de voleibol - Posicionamento P1 a P6">
      <rect x="15" y="15" width="330" height="185" rx="6" fill="var(--court)" stroke="#FFFFFF" stroke-width="3"/>
      <line x1="15" y1="18" x2="345" y2="18" stroke="#FFFFFF" stroke-width="4"/>
      <line x1="15" y1="20" x2="345" y2="20" stroke="rgba(0,0,0,0.25)" stroke-width="2" stroke-dasharray="4 2"/>
      <line x1="15" y1="98" x2="345" y2="98" stroke="#FFFFFF" stroke-width="2" stroke-dasharray="6 4"/>
      <text x="180" y="12" text-anchor="middle" fill="var(--text-muted)" font-family="var(--mono)" font-size="9" font-weight="800">▲ REDE / BLOQUEIO ▲</text>
      <text x="340" y="93" text-anchor="end" fill="rgba(255,255,255,0.7)" font-family="var(--mono)" font-size="8.5" font-weight="700">LINHA DOS 3M</text>
      <text x="25" y="190" text-anchor="start" fill="rgba(255,255,255,0.85)" font-family="var(--cond)" font-size="11" font-weight="800">${esc(homeLabel)}</text>
      <text x="180" y="208" text-anchor="middle" fill="var(--text-muted)" font-family="var(--mono)" font-size="8.5" font-weight="700">
        Levantadora na zona ${selected} · ${isFrontSetter ? 'rede' : 'fundo'}
      </text>
      ${circles}
    </svg>
  `;
}

function renderTeamsPage() {
  const c = C();
  if (!c) return '<p class="empty">Sem dados de equipes.</p>';
  const teams = c.teams || [];
  if (!state.team && teams.length) state.team = teams[0].team;

  const t = teams.find(x => x.team === state.team) || teams[0];
  if (!t) return '<p class="empty">Não há equipes disponíveis nesta competição.</p>';
  const at = atlasTeam(t.team);
  const activeSection = state.teamSection || 'Visão geral';

  return `
    <div>
      <label class="team-picker">Equipe
        <select id="team-picker" aria-label="Selecionar equipe">
          ${teams.map(x => `<option value="${esc(x.team)}" ${x.team === t.team ? 'selected' : ''}>${esc(teamName(x.team))}</option>`).join('')}
        </select>
      </label>

      <!-- Team Identity Hero -->
      <div class="team-hero-card">
        <div class="hero-top">
          <div>
            <h1 style="margin:0;">${esc(teamName(t.team))}</h1>
            <span style="font-size:12px;color:#94A3B8;">${esc(competitionLabel(c))} · ${esc(seasonLabel(c.season))}</span>
          </div>
          <div class="record-badge">${t.wins}V – ${t.losses}D</div>
        </div>

        <!-- Identity Metrics -->
        <div class="identity-metrics-grid">
          <div class="identity-card" onclick="openMetricSheet('so');">
            <div class="lbl">Side-Out</div>
            <div class="val">${pct(t.metrics.so.value)}</div>
            <div class="delta">${signed(t.metrics.so.delta)} pp</div>
          </div>
          <div class="identity-card" onclick="openMetricSheet('bp');">
            <div class="lbl">Break Point</div>
            <div class="val">${pct(t.metrics.bp.value)}</div>
            <div class="delta">${signed(t.metrics.bp.delta)} pp</div>
          </div>
          <div class="identity-card" onclick="openMetricSheet('pos_rec');">
            <div class="lbl">K1+ Kill%</div>
            <div class="val">${pct(t.metrics.pos_rec?.value)}</div>
            <div class="delta">Passe A</div>
          </div>
          <div class="identity-card" onclick="openMetricSheet('neg_rec');">
            <div class="lbl">K1− Kill%</div>
            <div class="val">${pct(t.metrics.neg_rec?.value)}</div>
            <div class="delta">Fora sist.</div>
          </div>
          <div class="identity-card" onclick="openMetricSheet('trans');">
            <div class="lbl">Transição</div>
            <div class="val">${pct(t.metrics.trans?.value)}</div>
            <div class="delta">K2 Kill%</div>
          </div>
          <div class="identity-card" onclick="openMetricSheet('eff');">
            <div class="lbl">Eficiência</div>
            <div class="val">${pct(t.metrics.eff.value)}</div>
            <div class="delta">Ataque</div>
          </div>
        </div>
      </div>

      <!-- Horizontal Swipe Section Rail -->
      <div class="section-tabs-rail">
        ${['Visão geral', 'Rotações', 'Ataque', 'Passe', 'Atletas', 'Avançado'].map(sec => `
          <button type="button" class="section-tab-btn ${activeSection === sec ? 'active' : ''}" onclick="state.teamSection='${sec}';render();">
            ${sec}
          </button>
        `).join('')}
      </div>

      <!-- Sub-section Views -->
      ${renderTeamSubSection(t, at, activeSection)}
    </div>
  `;
}

function renderTeamSubSection(t, at, section) {
  if (section === 'Rotações') return renderTeamRotations(t, at);
  if (section === 'Atletas') return renderTeamAthletes(t);
  if (section === 'Ataque') return renderTeamAttack(t, at);
  if (section === 'Passe') return renderTeamReception(t);
  if (section === 'Avançado') return renderTeamAdvanced(t, at);

  // Visão geral default
  return `
    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;">
      <div class="rotation-widget-box">
        <h3>Perfil Ofensivo</h3>
        ${profile(t)}
      </div>
      <div class="rotation-widget-box">
        <h3>Resumo Tático</h3>
        ${teamSummary(t)}
      </div>
    </div>
  `;
}

// ROTAÇÕES P1–P6 COM LEVANTADORA FUNDO/REDE
function renderTeamRotations(t, at) {
  const p = state.rotation || 1;
  const rot = at?.rotations?.find(r => r.position === p);

  return `
    <div class="rotation-widget-box">
      <div class="rotation-controls">
        <!-- P1-P6 Horizontal Selector -->
        <div>
          <span style="font:800 11px var(--mono);text-transform:uppercase;color:var(--text-muted);display:block;margin-bottom:6px;">Passagem</span>
          <div class="p-selector">
            ${[1, 2, 3, 4, 5, 6].map(num => `
              <button type="button" class="p-btn ${p === num ? 'active' : ''}" onclick="state.rotation=${num};render();">P${num}</button>
            `).join('')}
          </div>
        </div>

      </div>

      <p class="note">P1 a P6 indicam a zona da levantadora no momento da rotação. P1, P6 e P5 ficam no fundo; P2, P3 e P4, na rede. A quadra é esquemática e não mostra a formação completa.</p>
      <!-- Court Visualizer -->
      <div class="court-frame">
        ${VolleyballCourt({
          rotations: at?.rotations || [],
          layer: state.layer || 'so',
          homeLabel: teamName(t.team),
          selected: p
        })}
      </div>

      <!-- Rotation Metrics -->
      ${rot ? `
        <div class="athlete-big-stats" style="grid-template-columns:repeat(auto-fit, minmax(100px, 1fr));">
          <div class="stat-box" onclick="openMetricSheet('so');">
            <span class="lbl">Side-Out</span>
            <span class="val">${pct(rot.so?.value)}</span>
            <span class="pct-pill">${signed(rot.so_delta_team)} pp vs time</span>
          </div>
          <div class="stat-box" onclick="openMetricSheet('bp');">
            <span class="lbl">Break Point</span>
            <span class="val">${pct(rot.bp?.value)}</span>
            <span class="pct-pill">${signed(rot.bp_delta_team)} pp vs time</span>
          </div>
          <div class="stat-box">
            <span class="lbl">Volume</span>
            <span class="val">${num(rot.so?.n || 0)}</span>
            <span class="pct-pill">rallies em recepção</span>
          </div>
          <div class="stat-box">
            <span class="lbl">Δ Liga</span>
            <span class="val">${signed(rot.so_delta_competition)} pp</span>
            <span class="pct-pill">vs média da liga</span>
          </div>
        </div>
      ` : '<p class="empty">Dados detalhados desta passagem indisponíveis nesta amostra.</p>'}
    </div>
  `;
}

function renderTeamAttack(t, at) {
  const model = t.presumed_distribution;
  const cal = model?.calibration;
  const lines = (model?.distribution || []).map(item => `<div class="prob-row"><span>${esc(teamName(item.name))} <small>(${num(item.attempts)} ataques · bruto ${pct(100*item.attempts/model.attempts)})</small></span><strong>${pct(100*item.probability)}</strong></div><div style="height:6px;border-radius:4px;background:var(--border);margin:4px 0 12px"><div style="height:100%;border-radius:4px;background:var(--primary);width:${Math.max(0,Math.min(100,100*item.probability))}%"></div></div>`).join('');
  const names = {positive:'Recepção positiva (K1+)',negative:'Recepção negativa (K1−)',transition:'Transição (K2)'};
  const phasesHtml = Object.entries(names).map(([key,label]) => {
    const phase = model?.phase_scenarios?.[key];
    const items = phase?.distribution || [];
    return `<details class="block"><summary>${esc(label)} · ${num(phase?.attempts || 0)} ataques</summary>${items.length ? `<p class="note">Cenário proporcional dentro de cada partida; não há registros de quem atacou em cada fase.</p><div class="table-wrap"><table><thead><tr><th>Atleta</th><th>Cenário</th><th>Faixa possível</th></tr></thead><tbody>${items.map(x=>`<tr><td>${esc(teamName(x.name))}</td><td>${pct(100*x.scenario)}</td><td>${pct(100*x.minimum)}–${pct(100*x.maximum)}</td></tr>`).join('')}</tbody></table></div><p class="note">${num(phase.games)} partidas reconciliadas · ${num(phase.excluded_games)} excluídas por dados incompletos ou totais divergentes. A faixa mostra os valores possíveis com os totais disponíveis; não é intervalo de confiança. Extremos das atletas podem não ocorrer simultaneamente.</p>`:'<p class="empty">Sem dados reconciliados suficientes nesta fase.</p>'}</details>`;
  }).join('');
  const rotations = at?.distribution_model || [];
  const rotationHtml = rotations.length ? rotations.map(r=>`<details class="block"><summary>P${num(r.position)} · ${num(r.availability_rallies)} rallies com formação reconciliada</summary><p class="note">Formação histórica mais frequente: ${num(r.n_lineup)} rallies. Cobertura total desta rotação: ${num(r.source_match_count)} partidas. Pesos relativos ao volume de ataques da temporada entre atletas dessa formação; não são levantamentos observados nessa rotação.</p>${(r.distribution||[]).filter(x=>x.weight>0).sort((a,b)=>b.weight-a.weight).map(x=>`<div class="prob-row"><span>${esc(teamName(x.name))}</span><strong>${pct(100*x.weight)}</strong></div>`).join('')}</details>`).join('') : '<p class="empty">Sem formação reconciliada suficiente para uma hipótese por rotação.</p>';
  return `<div class="rotation-widget-box">
      <h3>Distribuição presumida <span class="pct-pill">Experimental</span></h3>
      ${model ? `<p>Participação ofensiva estimada para a equipe nesta temporada.</p><div class="probabilities">${lines}</div><p class="note">${num(model.attempts)} ataques individuais · ${num(model.games)} partidas. Prior simétrico: ${fmt(model.strength,1)} ataques equivalentes. Concentração: ${fmt(model.predictability,1)}/100, entre atletas registradas; não é certeza sobre a próxima bola.</p><p class="note">${cal?.calibrated ? `Força da suavização escolhida em ${num(cal.evaluated_games)} jogos do mesmo recorte (${num(cal.evaluated_attempts)} ataques avaliáveis). Ainda requer avaliação independente.` : 'Força da suavização provisória: amostra insuficiente para calibrar.'}</p>` : '<p class="empty">Sem pelo menos duas atacantes com ataques registrados neste recorte.</p>'}
      <h3>Cenários por fase</h3><p class="note">Os relatórios trazem totais por atleta e por fase em cada jogo. O cenário supõe que a participação de cada atleta foi igual nas três fases dentro de cada partida. É uma hipótese, não um efeito de passe aprendido; os limites mostram a incerteza dos dados agregados.</p>${phasesHtml}
      <h3>Hipóteses por rotação</h3>${rotationHtml}
      <p class="note">A base não identifica a levantadora que fez cada distribuição nem a atacante em cada fase. As opções acima não equivalem à presença atual em quadra.</p>
      <h3>Eficiência e kills por fase de jogo</h3>${phases(t)}</div>`;
}

function renderTeamReception(t) {
  const metrics = t.metrics || {};
  return `<section class="rotation-widget-box"><h3>Recepção</h3><div class="athlete-big-stats">${[['positive','Recepção positiva'],['excellent','Recepção excelente'],['rec_error','Erros de recepção']].map(([key,label]) => `<div class="stat-box"><span class="lbl">${label}</span><span class="val">${pct(metrics[key]?.value)}</span><span class="pct-pill">${num(metrics[key]?.n || 0)} recepções</span></div>`).join('')}</div><p class="note">Os valores dependem da cobertura dos relatórios disponíveis.</p></section>`;
}

function renderTeamAthletes(t) {
  return `
    <div class="rotation-widget-box">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3>Atletas da Equipe</h3>
        <button type="button" class="btn-chip" onclick="loadAllTeamAthletes('${esc(t.team)}');">Carregar Elenco Completo</button>
      </div>
      <div class="table-wrap">
        <table class="responsive-table">
          <thead>
            <tr>
              <th>Atleta</th>
              <th class="num">Pontos</th>
              <th class="num">Kill%</th>
              <th class="num">Eficiência</th>
              <th class="num">Ações</th>
            </tr>
          </thead>
          <tbody>
            ${(t.athletes || []).map(a => `
              <tr>
                <td data-label="Atleta">
                  <button type="button" class="athlete-link" data-open-athlete="${esc(a.name)}" data-athlete-team="${esc(t.team)}">${esc(teamName(a.name))} <span aria-hidden="true">→</span></button>
                </td>
                <td data-label="Pontos" class="num numeric"><strong>${num(a.points || 0)}</strong></td>
                <td data-label="Kill%" class="num">${pct(a.kill || a.metrics?.kill?.value)}</td>
                <td data-label="Eficiência" class="num">${pct(a.eff || a.metrics?.eff?.value)}</td>
                <td data-label="Ações" class="num">
                  <button type="button" class="btn-chip" data-add-compare-athlete="${esc(a.name)}" data-team="${esc(t.team)}">+ Comparar</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderTeamAdvanced(t, at) {
  const matrix = at?.matrix || [];
  const runs = at?.serve_runs || {};
  const matrixRows = [1,2,3,4,5,6].map(own => `<tr><th scope="row">P${own}</th>${[1,2,3,4,5,6].map(other => {
    const cell = matrix.find(item => item.own === own && item.other === other);
    const m = cell?.so;
    return `<td>${m?.n ? `${pct(m.value)} <small>(${num(m.n)})</small>` : '—'}</td>`;
  }).join('')}</tr>`).join('');
  return `
    <section class="rotation-widget-box">
      <h3>Análise avançada</h3>
      <p class="note">Side-out por rotação da sua equipe e do adversário. O número entre parênteses é a quantidade de rallies observados.</p>
      ${matrix.some(cell => cell.so?.n) ? `<div class="table-wrap"><table class="advanced-matrix"><thead><tr><th>Equipe / rival</th>${[1,2,3,4,5,6].map(p=>`<th>P${p}</th>`).join('')}</tr></thead><tbody>${matrixRows}</tbody></table></div>` : '<p class="empty">Ainda não há amostra de rotações para montar a matriz.</p>'}
      <h3>Passagens de saque</h3>
      <p>${runs.n ? `Média de ${fmt(runs.mean)} pontos por passagem completa · ${num(runs.n)} passagens.` : 'Sem passagens de saque suficientes para esta equipe.'}</p>
      <p class="note">Passagens encerradas pelo fim do set são excluídas da média.</p>
      <button type="button" class="btn-primary" data-load-lineups="${esc(t.team)}">Ver análise de presença</button>
      <div id="tactical-lineups-container" aria-live="polite"></div>
    </section>`;
}

// 9. SCREEN 4: ATHLETES PAGE (ATLETAS)
function renderAthletesPage() {
  const c = C();
  if (!c) return '<p class="empty">Sem dados de atletas.</p>';

  // Flatten available athletes across teams
  const allAthletes = [];
  (c.teams || []).forEach(t => {
    (t.athletes || []).forEach(a => {
      allAthletes.push({ ...a, teamName: t.team });
    });
  });

  // Filter by query and position
  const q = normalized(state.athleteQuery);
  const filtered = allAthletes.filter(a => {
    if (q && !normalized(`${a.name} ${a.teamName}`).includes(q)) return false;
    return true;
  });

  filtered.sort((a,b) => (b.points || 0) - (a.points || 0));
  const leadAthlete = allAthletes.find(a => a.name === state.athleteName && a.teamName === state.athleteTeam) || filtered[0];

  return `
    <div>
      <div class="section-head">
        <h1>Atletas</h1>
        <span class="rule"></span>
        <small>${esc(competitionLabel(c))}</small>
      </div>

      <!-- Search Bar -->
      <div style="margin-bottom:16px;">
        <input type="search" id="athlete-live-search" value="${esc(state.athleteQuery)}" placeholder="Buscar por nome da atleta ou equipe..." style="width:100%;height:44px;border:1px solid var(--border);border-radius:8px;padding:0 14px;background:var(--surface);">
      </div>

      <!-- Featured / Selected Athlete Profile -->
      ${leadAthlete ? renderAthleteProfile(leadAthlete) : '<p class="empty">Nenhum atleta encontrado.</p>'}

      <!-- Athlete Roster Table / Cards -->
      <div class="rotation-widget-box">
        <h3>Atletas e rankings</h3>
        <p class="note" id="athlete-loading-status">${athleteLoadState.get(c.id) === 'loading' ? 'Carregando todas as atletas…' : athleteLoadState.get(c.id) === 'failed' ? 'Não foi possível carregar todos os perfis. ' : ''}${athleteLoadState.get(c.id) === 'failed' ? '<button type="button" id="retry-athletes">Tentar novamente</button>' : ''}</p>
        <div class="table-wrap">
          <table class="responsive-table">
            <thead>
              <tr>
                <th>Atleta</th>
                <th>Equipe</th>
                <th class="num">Pontos</th>
                <th class="num">Kill%</th>
                <th class="num">Eficiência</th>
                <th class="num">Ações</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.map(a => `
                <tr data-athlete-name="${esc(a.name)}" data-athlete-team="${esc(a.teamName)}">
                  <td data-label="Atleta"><button type="button" class="athlete-link" data-open-athlete="${esc(a.name)}" data-athlete-team="${esc(a.teamName)}">${esc(teamName(a.name))} <span aria-hidden="true">→</span></button></td>
                  <td data-label="Equipe">${esc(teamName(a.teamName))}</td>
                  <td data-label="Pontos" class="num numeric"><strong>${num(a.points || 0)}</strong></td>
                  <td data-label="Kill%" class="num">${pct(a.kill || a.metrics?.kill?.value)}</td>
                  <td data-label="Eficiência" class="num">${pct(a.eff || a.metrics?.eff?.value)}</td>
                  <td data-label="Ações" class="num">
                    <button type="button" class="btn-chip" data-add-compare-athlete="${esc(a.name)}" data-team="${esc(a.teamName)}">+ Comparar</button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// LAYERED ATHLETE PROFILE VIEW
function renderAthleteProfile(a) {
  const killVal = a.kill ?? a.metrics?.kill?.value;
  const effVal = a.eff ?? a.metrics?.eff?.value;
  const posVal = a.positive ?? a.metrics?.positive?.value;

  return `
    <div class="athlete-profile-card" id="athlete-profile" tabindex="-1">
      <div class="athlete-top">
        <div class="athlete-avatar" style="width:54px;height:54px;font-size:22px;">${esc(a.name?.charAt(0) || 'A')}</div>
        <div class="athlete-title">
          <h2 class="name" style="margin:0;">${esc(teamName(a.name))}</h2>
          <span class="role">${esc(teamName(a.teamName || a.team))} · ${num(a.games || 1)} jogos disputados</span>
        </div>
      </div>

      <!-- Grande Destaque -->
      <div class="athlete-big-stats">
        <div class="stat-box" onclick="openMetricSheet('kill');">
          <span class="lbl">Pontos / Jogo</span>
          <span class="val">${fmt((a.points || 0) / Math.max(1, a.games || 1))}</span>
          <span class="pct-pill">${num(a.points || 0)} pts totais</span>
        </div>
        <div class="stat-box" onclick="openMetricSheet('eff');">
          <span class="lbl">Eficiência</span>
          <span class="val">${pct(effVal)}</span>
          <span class="pct-pill">Ataque líquido</span>
        </div>
        <div class="stat-box" onclick="openMetricSheet('kill');">
          <span class="lbl">Kill%</span>
          <span class="val">${pct(killVal)}</span>
          <span class="pct-pill">Finalizações</span>
        </div>
      </div>

      <!-- Horizontal Metrics Carousel (Draggable) -->
      <div class="section-head" style="margin-top:16px;">
        <h3>Fundamentos Técnicos</h3>
        <span class="rule"></span>
        <small>toque no card para ver cálculo</small>
      </div>
      <div class="metric-carousel">
        <div class="metric-card-interactive" onclick="openMetricSheet('kill');">
          <div class="category">Ataque</div>
          <div class="primary-num">${pct(killVal)}</div>
          <div class="sub-detail">Kill% · Finalização</div>
        </div>
        <div class="metric-card-interactive" onclick="openMetricSheet('positive');">
          <div class="category">Passe</div>
          <div class="primary-num">${pct(posVal)}</div>
          <div class="sub-detail">Recepção Positiva</div>
        </div>
        <div class="metric-card-interactive" onclick="openMetricSheet('eff');">
          <div class="category">Eficiência</div>
          <div class="primary-num">${pct(effVal)}</div>
          <div class="sub-detail">Saldo de ataque</div>
        </div>
        <div class="metric-card-interactive" onclick="openMetricSheet('block');">
          <div class="category">Bloqueio</div>
          <div class="primary-num">${a.blocks == null ? '—' : num(a.blocks)}</div>
          <div class="sub-detail">Pontos de bloqueio</div>
        </div>
      </div>

      <div style="margin-top:16px;display:flex;justify-content:flex-end;">
        <button type="button" class="btn-primary" data-add-compare-athlete="${esc(a.name)}" data-team="${esc(a.teamName || a.team)}">+ Adicionar à Comparação</button>
      </div>
    </div>
  `;
}

// 10. ATHLETE COMPARISON MODAL / VIEW
function openAthleteComparison(a, b) {
  const html = `
    <div class="comparison-view">
      <div class="athlete-big-stats" style="grid-template-columns:1fr 1fr;">
        <div class="stat-box">
          <span class="lbl">${esc(teamName(a.team))}</span>
          <strong style="font-size:16px;">${esc(teamName(a.name))}</strong>
        </div>
        <div class="stat-box" style="text-align:right;">
          <span class="lbl">${esc(teamName(b.team))}</span>
          <strong style="font-size:16px;">${esc(teamName(b.name))}</strong>
        </div>
      </div>

      <div class="table-wrap" style="margin-top:16px;">
        <table>
          <thead>
            <tr>
              <th>Métrica</th>
              <th class="num">${esc(teamName(a.name))}</th>
              <th class="num">${esc(teamName(b.name))}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Pontos Totais</td>
              <td class="num numeric"><strong>${num(a.points || 0)}</strong></td>
              <td class="num numeric"><strong>${num(b.points || 0)}</strong></td>
            </tr>
            <tr>
              <td>Kill% de Ataque</td>
              <td class="num">${pct(a.kill || a.metrics?.kill?.value)}</td>
              <td class="num">${pct(b.kill || b.metrics?.kill?.value)}</td>
            </tr>
            <tr>
              <td>Eficiência Ofensiva</td>
              <td class="num">${pct(a.eff || a.metrics?.eff?.value)}</td>
              <td class="num">${pct(b.eff || b.metrics?.eff?.value)}</td>
            </tr>
            <tr>
              <td>Passe Positivo</td>
              <td class="num">${pct(a.positive || a.metrics?.positive?.value)}</td>
              <td class="num">${pct(b.positive || b.metrics?.positive?.value)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  BottomSheet.open({
    title: 'Comparação de Atletas',
    subtitle: `${teamName(a.name)} × ${teamName(b.name)}`,
    contentHtml: html
  });
}

// ON-DEMAND DATA LOADING HELPERS
async function loadMatchDetails(matchId) {
  const allDetails = await DataLoader.load('matches');
  if (allDetails && allDetails[String(matchId)]) {
    const c = C();
    if (!c.match_details) c.match_details = {};
    c.match_details[String(matchId)] = allDetails[String(matchId)];
    render();
  }
}

async function loadAllTeamAthletes(teamName) {
  const allAthletes = await DataLoader.load('athletes');
  const c = C();
  if (allAthletes && allAthletes[c.id] && allAthletes[c.id][teamName]) {
    const t = c.teams.find(x => x.team === teamName);
    if (t) {
      t.athletes = allAthletes[c.id][teamName];
      render();
    }
  }
}

const athleteLoadState = new Map();
async function loadAllAthletes() {
  const cohort = C();
  if (!cohort || ['loading','loaded'].includes(athleteLoadState.get(cohort.id))) return;
  athleteLoadState.set(cohort.id, 'loading');
  if (state.page === 'Atletas') render();
  const roster = await DataLoader.load('athletes');
  if (!roster?.[cohort.id]) {
    athleteLoadState.set(cohort.id, 'failed');
  } else {
    for (const team of cohort.teams || []) {
      if (Array.isArray(roster[cohort.id][team.team])) team.athletes = roster[cohort.id][team.team];
    }
    athleteLoadState.set(cohort.id, 'loaded');
  }
  if (C() === cohort && state.page === 'Atletas') render();
}

async function loadTacticalLineups(teamName) {
  const cohort = C();
  const container = $('#tactical-lineups-container');
  if (!container) return;
  container.innerHTML = '<p class="note">Carregando análise de presença…</p>';
  const tac = await DataLoader.load('tactical');
  if (C() !== cohort || state.page !== 'Times' || state.team !== teamName || state.teamSection !== 'Avançado') return;
  const data = tac?.[cohort.id]?.teams?.[teamName];
  const onoff = data?.on_off || [];
  container.innerHTML = onoff.length ? `<h4>Presença em quadra</h4><p class="note">Comparação descritiva, não indica causa. Percentuais de pontos ganhos com e sem a atleta em quadra; amostra entre parênteses.</p><div class="table-wrap"><table><thead><tr><th>Atleta</th><th>Com</th><th>Sem</th></tr></thead><tbody>${onoff.map(a => `<tr><td>${esc(a.player)}</td><td>${pct(a.on?.value)} (${num(a.on?.n || 0)})</td><td>${pct(a.off?.value)} (${num(a.off?.n || 0)})</td></tr>`).join('')}</tbody></table></div>` : `<p class="note">${data ? 'Não há amostra confiável de presença para esta equipe.' : 'Não foi possível carregar os dados de presença. Tente novamente.'}</p>`;
}

// 11. GLOBAL SEARCH
function setupGlobalSearch() {
  const input = $('#global-search');
  const dropdown = $('#global-search-results');
  if (!input || !dropdown) return;

  input.oninput = () => {
    const q = normalized(input.value.trim());
    if (!q) {
      dropdown.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      return;
    }

    const c = C();
    const results = [];

    // Search teams
    (c.teams || []).forEach(t => {
      if (normalized(t.team).includes(q)) {
        results.push({ type: 'team', label: teamName(t.team), id: t.team });
      }
    });

    // Search athletes
    (c.teams || []).forEach(t => {
      (t.athletes || []).forEach(a => {
        if (normalized(a.name).includes(q)) {
          results.push({ type: 'athlete', label: teamName(a.name), sub: teamName(t.team), id: a.name, team: t.team });
        }
      });
    });

    // Search matches
    (c.matches || []).forEach(m => {
      if (normalized(`${m.home_team} ${m.away_team} ${m.match_id}`).includes(q)) {
        results.push({ type: 'match', label: `${teamName(m.home_team)} × ${teamName(m.away_team)}`, sub: matchDate(m.date), id: m.match_id });
      }
    });

    if (results.length === 0) {
      dropdown.innerHTML = '<p style="padding:12px;margin:0;color:var(--text-muted);font-size:12px;">Nenhum resultado encontrado.</p>';
    } else {
      dropdown.innerHTML = results.slice(0, 8).map(r => `
        <button type="button" class="search-item" data-search-type="${r.type}" data-search-id="${esc(r.id)}" data-search-team="${esc(r.team || '')}">
          <div>
            <strong>${esc(r.label)}</strong>
            ${r.sub ? `<span style="font-size:11px;color:var(--text-muted);display:block;">${esc(r.sub)}</span>` : ''}
          </div>
          <span class="type-badge ${r.type}">${r.type}</span>
        </button>
      `).join('');

      dropdown.querySelectorAll('.search-item').forEach(btn => {
        btn.onclick = () => {
          dropdown.hidden = true;
          input.value = '';
          const type = btn.dataset.searchType;
          const id = btn.dataset.searchId;
          if (type === 'team') {
            state.team = id;
            navigateTo('Times');
          } else if (type === 'athlete') {
            state.team = btn.dataset.searchTeam;
            state.athleteQuery = id;
            navigateTo('Atletas');
          } else if (type === 'match') {
            navigateTo('Jogos', id);
          }
        };
      });
    }

    dropdown.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  };

  document.addEventListener('click', e => {
    if (!e.target.closest('.global-search-bar')) {
      dropdown.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }
  });
}

function selectQuickCompetition(competition, gender) {
  const current = C();
  const candidates = DATA.cohorts.filter(c => c.competition === competition && c.gender === gender);
  const notice = $('#filter-notice');
  if (!candidates.length) {
    if (notice) {
      notice.textContent = `${competition === 'CBS' ? 'CBS' : 'Superliga'} ${gender} não está disponível na base ainda.`;
      notice.hidden = false;
    }
    return false;
  }
  const sameSeason = current?.competition === competition && candidates.find(c => c.season === current.season && c.category === current.category);
  const sorted = [...candidates].sort((a, b) => String(b.season || '').localeCompare(String(a.season || '')));
  const selected = sameSeason || sorted.find(c => c.edition_status === 'CURRENT') || sorted[0];
  state.cohort = DATA.cohorts.indexOf(selected);
  if (state.page === 'Atletas') queueMicrotask(loadAllAthletes);
  state.team = ''; state.opponent = ''; state.query = ''; state.athleteQuery = ''; state.athleteName = null; state.athleteTeam = null; state.matchId = null;
  if (notice) { notice.textContent = ''; notice.hidden = true; }
  render();
  return true;
}

// 12. RENDER PIPELINE
function render() {
  const c = C();
  if (!c) {
    $('#main').innerHTML = '<h1>Sem coortes disponíveis</h1>';
    return;
  }

  // Quick Filter Chips update
  const chipsRail = $('#quick-filter-chips');
  if (chipsRail) {
    chipsRail.innerHTML = `
      <button type="button" class="chip-btn ${c.competition === 'SUPERLIGA' && c.gender === 'masculino' ? 'active' : ''}" onclick="selectQuickCompetition('SUPERLIGA', 'masculino');">Superliga Masc</button>
      <button type="button" class="chip-btn ${c.competition === 'SUPERLIGA' && c.gender === 'feminino' ? 'active' : ''}" onclick="selectQuickCompetition('SUPERLIGA', 'feminino');">Superliga Fem</button>
      <button type="button" class="chip-btn ${c.competition === 'CBS' && c.gender === 'masculino' ? 'active' : ''}" onclick="selectQuickCompetition('CBS', 'masculino');">CBS Masc</button>
      <button type="button" class="chip-btn ${c.competition === 'CBS' && c.gender === 'feminino' ? 'active' : ''}" onclick="selectQuickCompetition('CBS', 'feminino');">CBS Fem</button>
      <button type="button" class="chip-btn more-filters" onclick="openFiltersSheet();">+ Filtros (${esc(seasonLabel(c.season))})</button>
    `;
  }

  // Sync Status Badge update
  const statusBadge = $('#sync-status-badge');
  const statusSub = $('#sync-status-sub');
  if (statusBadge && statusSub) {
    const h = DATA.sync_health || {};
    const count = h.database_match_count ?? (c.matches || []).length;
    const status = effectiveSyncStatus(h);
    const label = $('#sync-status-label');
    const dot = $('#sync-status-dot');
    if (label) label.textContent = ({HEALTHY:'Coleta recente', DEGRADED:'Coleta parcial', STALE:'Coleta atrasada', FAILED:'Falha na coleta', UNKNOWN:'Não confirmado'})[status];
    if (dot) dot.className = `status-dot ${status === 'UNKNOWN' ? 'degraded' : status.toLowerCase()}`;
    statusSub.textContent = `${count} jogos`;
    statusBadge.onclick = openSyncHealthSheet;
  }

  // Active page render
  const main = $('#main');
  if (state.page === 'Início') {
    main.innerHTML = renderHomeFeed();
  } else if (state.page === 'Jogos') {
    main.innerHTML = renderMatchesPage();
  } else if (state.page === 'Times') {
    main.innerHTML = renderTeamsPage();
  } else if (state.page === 'Atletas') {
    main.innerHTML = renderAthletesPage();
  } else if (state.page === 'Confrontos') {
    main.innerHTML = confrontation();
  } else {
    main.innerHTML = renderHomeFeed();
  }

  bindInteractions();
}

// BIND INTERACTIVE ACTIONS
function bindInteractions() {
  // Navigation tabs
  document.querySelectorAll('[data-nav]').forEach(btn => {
    btn.onclick = () => navigateTo(btn.dataset.nav);
  });

  // Match links
  document.querySelectorAll('[data-match]').forEach(el => {
    el.onclick = () => {
      navigateTo('Jogos', el.dataset.match);
    };
  });

  // Team links
  document.querySelectorAll('[data-team]').forEach(el => {
    if (el.tagName.toLowerCase() !== 'circle') {
      el.onclick = () => {
        state.team = el.dataset.team;
        navigateTo('Times');
      };
    }
  });

  const picker = $('#team-picker');
  if (picker) picker.onchange = e => { state.team = e.target.value; render(); };
  document.querySelectorAll('[data-open-athlete]').forEach(el => {
    el.onclick = e => {
      e.stopPropagation();
      state.athleteName = el.dataset.openAthlete;
      state.athleteTeam = el.dataset.athleteTeam;
      state.athleteQuery = '';
      navigateTo('Atletas');
      $('#athlete-profile')?.scrollIntoView({block:'start'});
    };
  });
  document.querySelectorAll('[data-load-lineups]').forEach(el => {
    el.onclick = () => loadTacticalLineups(el.dataset.loadLineups);
  });
  const retryAthletes = $('#retry-athletes');
  if (retryAthletes) retryAthletes.onclick = () => loadAllAthletes();

  // Match filters
  document.querySelectorAll('[data-match-filter]').forEach(btn => {
    btn.onclick = () => {
      state.matchFilter = btn.dataset.matchFilter;
      render();
    };
  });

  // Add to compare (Athletes)
  document.querySelectorAll('[data-add-compare-athlete]').forEach(btn => {
    btn.onclick = e => {
      e.stopPropagation();
      const name = btn.dataset.addCompareAthlete;
      const team = btn.dataset.team;
      CompareManager.add({ id: name, name, team, type: 'athlete' });
    };
  });

  // Add to compare (Teams)
  document.querySelectorAll('[data-add-compare-team]').forEach(btn => {
    btn.onclick = e => {
      e.stopPropagation();
      const team = btn.dataset.addCompareTeam;
      CompareManager.add({ id: team, name: team, team, type: 'team' });
    };
  });

  // Live athlete search
  const athSearch = $('#athlete-live-search');
  if (athSearch) {
    athSearch.oninput = e => {
      state.athleteQuery = e.target.value;
      state.athleteName = null; state.athleteTeam = null;
      const pos = e.target.selectionStart;
      render();
      const cur = $('#athlete-live-search');
      if (cur) { cur.focus(); cur.setSelectionRange(pos, pos); }
    };
  }

  // Open confrontation shortcut
  document.querySelectorAll('[data-open-confronto]').forEach(btn => {
    btn.onclick = () => {
      state.team = btn.dataset.openConfronto;
      state.opponent = btn.dataset.openOpponent;
      state.page = 'Confrontos';
      render();
    };
  });
}

// INITIALIZATION
document.addEventListener('DOMContentLoaded', () => {
  BottomSheet.init();
  CompareManager.init();
  setupGlobalSearch();
  render();
});
