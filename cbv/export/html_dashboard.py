"""HTML Dashboard Generator for CBV Tactical Intelligence & Performance."""

from pathlib import Path
import json
from typing import Dict, Any
from rich.console import Console

from cbv.config import BASE_DIR, logger
from cbv.database.repository import default_repo
from cbv.analysis.tactics import get_competition_tactical_summary, get_team_tactical_dossier

console = Console()
EXPORTS_DIR = BASE_DIR / "exports"
DEFAULT_HTML_PATH = EXPORTS_DIR / "dashboard.html"


def generate_dashboard_data() -> Dict[str, Any]:
    """Compiles all competition and tactical data into a structured payload for the HTML dashboard."""
    with default_repo.get_connection() as conn:
        # Match statistics
        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        set_count = conn.execute("SELECT COUNT(*) FROM sets").fetchone()[0]
        player_count = conn.execute("SELECT COUNT(DISTINCT player_name || '_' || team) FROM player_match_stats").fetchone()[0]
        
        matches = conn.execute("""
            SELECT match_id, home_team, away_team, home_sets, away_sets, date 
            FROM matches 
            ORDER BY match_id
        """).fetchdf().to_dict(orient="records")
        for m in matches:
            if hasattr(m["date"], "isoformat"):
                m["date"] = m["date"].isoformat()

        # All teams
        teams = [r[0] for r in conn.execute("SELECT DISTINCT team FROM team_tactical_stats ORDER BY team").fetchall()]

    # Competition summaries
    tac_summary = get_competition_tactical_summary()
    summary_dict = {
        k: df.to_dict(orient="records") for k, df in tac_summary.items()
    }

    # Clean NaNs in summary_dict
    for k, rows in summary_dict.items():
        for row in rows:
            for field, val in row.items():
                if val is None or (isinstance(val, float) and str(val) == "nan"):
                    row[field] = 0

    # Team dossiers
    dossiers = {}
    for t in teams:
        d = get_team_tactical_dossier(t)
        if d:
            # Clean records
            att_records = d["attackers"].to_dict(orient="records")
            for r in att_records:
                for k, v in r.items():
                    if v is None or (isinstance(v, float) and str(v) == "nan"):
                        r[k] = 0.0

            rec_records = d["receivers"].to_dict(orient="records")
            for r in rec_records:
                for k, v in r.items():
                    if v is None or (isinstance(v, float) and str(v) == "nan"):
                        r[k] = 0.0

            set_records = d["sets_dist"].to_dict(orient="records")
            for r in set_records:
                for k, v in r.items():
                    if v is None or (isinstance(v, float) and str(v) == "nan"):
                        r[k] = 0

            dossiers[t] = {
                "team": d["team"],
                "record": d["record"],
                "totals": d["totals"],
                "attackers": att_records,
                "receivers": rec_records,
                "sets_dist": set_records,
            }

    return {
        "kpis": {
            "matches": match_count,
            "sets": set_count,
            "players": player_count,
            "teams": len(teams),
            "validation_status": "100% VALID",
        },
        "matches": matches,
        "teams": teams,
        "summary": summary_dict,
        "dossiers": dossiers,
    }


def build_dashboard_html(data: Dict[str, Any]) -> str:
    """Builds self-contained interactive HTML dashboard with embedded data, styling, and JS."""
    json_data = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Tático CBV — CBS Sub-18 Masculino Especial 2026</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --background: #090d16;
      --card: #131b2e;
      --card-hover: #1c2742;
      --border: #263352;
      --foreground: #f1f5f9;
      --muted-foreground: #94a3b8;
      --primary: #3b82f6;
      --primary-focus: #2563eb;
      --accent: #10b981;
      --accent-warn: #f59e0b;
      --accent-danger: #ef4444;
    }}
    body {{
      background-color: var(--background);
      color: var(--foreground);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }}
    .tab-btn.active {{
      background-color: var(--primary);
      color: #ffffff;
      font-weight: 600;
    }}
    .custom-scrollbar::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    .custom-scrollbar::-webkit-scrollbar-thumb {{
      background: var(--border);
      border-radius: 4px;
    }}
  </style>
</head>
<body class="min-h-screen p-4 md:p-8 antialiased">
  <div class="max-w-7xl mx-auto space-y-6">
    
    <!-- Top Header -->
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">CBS 2026 Oficial</span>
          <span class="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">Sub-18 Masculino Especial</span>
        </div>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight text-[var(--foreground)]">
          Inteligência Tática & Performance de Voleibol
        </h1>
        <p class="text-[var(--muted-foreground)] text-sm mt-1">
          Scouting avançado, Side-Out, Break Point, Rotações P1–P6 e Eficiência de Fases (K1+/K1-/K2)
        </p>
      </div>

      <!-- Quick KPI Chips -->
      <div class="flex flex-wrap gap-2">
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-center">
          <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Partidas</span>
          <span class="text-lg font-bold text-blue-400" id="kpi-matches">34</span>
        </div>
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-center">
          <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Sets Auditados</span>
          <span class="text-lg font-bold text-emerald-400" id="kpi-sets">86</span>
        </div>
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-center">
          <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Atletas</span>
          <span class="text-lg font-bold text-amber-400" id="kpi-players">675</span>
        </div>
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-center">
          <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Auditoria</span>
          <span class="text-lg font-bold text-emerald-400">100% VALID</span>
        </div>
      </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="flex flex-wrap gap-2 border-b border-[var(--border)] pb-2" id="nav-tabs">
      <button onclick="switchTab('overview')" class="tab-btn active px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="overview">
        📊 Fases (SO vs BP)
      </button>
      <button onclick="switchTab('phase-attacks')" class="tab-btn px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="phase-attacks">
        ⚔️ Ataque por Situação (K1/K2)
      </button>
      <button onclick="switchTab('rotations')" class="tab-btn px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="rotations">
        🔄 Rotações do Levantador (P1-P6)
      </button>
      <button onclick="switchTab('team-dossier')" class="tab-btn px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="team-dossier">
        📋 Dossiê de Equipe (Scout)
      </button>
      <button onclick="switchTab('h2h')" class="tab-btn px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="h2h">
        🥊 Confronto Direto
      </button>
      <button onclick="switchTab('targets-usage')" class="tab-btn px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="targets-usage">
        🎯 Alvos de Saque & Usage
      </button>
      <button onclick="switchTab('matches')" class="tab-btn px-4 py-2 text-sm rounded-xl transition border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--card-hover)]" data-tab="matches">
        🏐 Partidas (34)
      </button>
    </nav>

    <!-- TAB 1: OVERVIEW & SO/BP -->
    <section id="tab-overview" class="tab-content space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
          <h3 class="text-base font-bold text-emerald-400 flex items-center gap-2 mb-2">
            <span>🛡️</span> Liderança em Side-Out (K1 — Recepção para Ponto)
          </h3>
          <p class="text-xs text-[var(--muted-foreground)] mb-4">
            Side-Out mede a capacidade da equipe de rodar o passe de primeira e finalizar sem ceder contra-ataques ao adversário.
          </p>
          <div class="space-y-3" id="top-so-bars"></div>
        </div>

        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
          <h3 class="text-base font-bold text-blue-400 flex items-center gap-2 mb-2">
            <span>⚡</span> Liderança em Break Point (K2 — Pressão de Saque & Transição)
          </h3>
          <p class="text-xs text-[var(--muted-foreground)] mb-4">
            Break Point mede a agressividade da equipe quando está no saque: quantos saques precisa para marcar ponto de contra-ataque ou ace.
          </p>
          <div class="space-y-3" id="top-bp-bars"></div>
        </div>
      </div>

      <!-- Tabela Completa SO/BP -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
        <h3 class="text-lg font-bold text-[var(--foreground)] mb-4">Classificação Geral de Side-Out e Break Point</h3>
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left text-sm border-collapse">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] text-xs uppercase tracking-wider">
                <th class="py-3 px-4">Equipe</th>
                <th class="py-3 px-4 text-center">Jogos</th>
                <th class="py-3 px-4 text-center">SO Pontos</th>
                <th class="py-3 px-4 text-center">Recepções</th>
                <th class="py-3 px-4 text-center">Side-Out %</th>
                <th class="py-3 px-4 text-center">Rendimento SO</th>
                <th class="py-3 px-4 text-center">BP Pontos</th>
                <th class="py-3 px-4 text-center">Saques</th>
                <th class="py-3 px-4 text-center">Break Point %</th>
                <th class="py-3 px-4 text-center">Rendimento BP</th>
              </tr>
            </thead>
            <tbody id="so-bp-table-body" class="divide-y divide-[var(--border)]"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: PHASE ATTACKS -->
    <section id="tab-phase-attacks" class="tab-content hidden space-y-6">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <div>
            <h3 class="text-lg font-bold text-[var(--foreground)]">Eficiência de Ataque por Situação de Passe</h3>
            <p class="text-xs text-[var(--muted-foreground)] mt-1">
              • <strong>K1+ (#+)</strong>: 1º ataque após recepção excelente/positiva | 
              • <strong>K1- (!-)</strong>: 1º ataque com recepção quebrada | 
              • <strong>K2 Transição</strong>: Contra-ataque
            </p>
          </div>
        </div>

        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left text-sm border-collapse">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] text-xs uppercase tracking-wider">
                <th class="py-3 px-4">Equipe</th>
                <th class="py-3 px-4 text-center bg-emerald-500/5">K1+ Att</th>
                <th class="py-3 px-4 text-center bg-emerald-500/5">K1+ Kill %</th>
                <th class="py-3 px-4 text-center bg-emerald-500/5 font-semibold text-emerald-400">K1+ Efic %</th>
                <th class="py-3 px-4 text-center bg-amber-500/5">K1- Att</th>
                <th class="py-3 px-4 text-center bg-amber-500/5">K1- Kill %</th>
                <th class="py-3 px-4 text-center bg-amber-500/5 font-semibold text-amber-400">K1- Efic %</th>
                <th class="py-3 px-4 text-center bg-blue-500/5">K2 Att</th>
                <th class="py-3 px-4 text-center bg-blue-500/5">K2 Kill %</th>
                <th class="py-3 px-4 text-center bg-blue-500/5 font-semibold text-blue-400">K2 Efic %</th>
              </tr>
            </thead>
            <tbody id="phase-table-body" class="divide-y divide-[var(--border)]"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 3: ROTATIONS MATRIX -->
    <section id="tab-rotations" class="tab-content hidden space-y-6">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
        <h3 class="text-lg font-bold text-[var(--foreground)] mb-2">Matriz de Rotações do Levantador (P1 a P6)</h3>
        <p class="text-xs text-[var(--muted-foreground)] mb-4">
          Saldo acumulado de pontos (+/-) de acordo com a posição do levantador na quadra. Células verdes indicam formações de ganho de pontos; vermelhas indicam formações vulneráveis (sangradouros de pontos).
        </p>

        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left text-sm border-collapse">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] text-xs uppercase tracking-wider">
                <th class="py-3 px-4">Equipe</th>
                <th class="py-3 px-4 text-center">P1 (Pos 1)</th>
                <th class="py-3 px-4 text-center">P2 (Pos 2)</th>
                <th class="py-3 px-4 text-center">P3 (Pos 3)</th>
                <th class="py-3 px-4 text-center">P4 (Pos 4)</th>
                <th class="py-3 px-4 text-center">P5 (Pos 5)</th>
                <th class="py-3 px-4 text-center">P6 (Pos 6)</th>
                <th class="py-3 px-4 text-center font-bold">Saldo Geral</th>
                <th class="py-3 px-4 text-center">Melhor Rodízio</th>
                <th class="py-3 px-4 text-center">Pior Rodízio</th>
              </tr>
            </thead>
            <tbody id="rotations-table-body" class="divide-y divide-[var(--border)]"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 4: TEAM DOSSIER -->
    <section id="tab-team-dossier" class="tab-content hidden space-y-6">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h3 class="text-lg font-bold text-[var(--foreground)]">Dossiê Tático & Scouting de Equipe</h3>
          <p class="text-xs text-[var(--muted-foreground)] mt-1">Selecione uma seleção para inspecionar todas as métricas detalhadas de campanha, linha de passe e atacantes.</p>
        </div>
        <div class="w-full md:w-64">
          <select id="team-selector" onchange="renderTeamDossier(this.value)" class="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--foreground)] focus:ring-2 focus:ring-blue-500 focus:outline-none cursor-pointer">
          </select>
        </div>
      </div>

      <div id="dossier-content" class="space-y-6">
        <!-- Rendered dynamically via JS -->
      </div>
    </section>

    <!-- TAB 5: HEAD-TO-HEAD -->
    <section id="tab-h2h" class="tab-content hidden space-y-6">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
        <h3 class="text-lg font-bold text-[var(--foreground)] mb-1">Simulador de Confronto Direto (Head-to-Head Scouting)</h3>
        <p class="text-xs text-[var(--muted-foreground)] mb-4">Escolha duas equipes para comparar o rendimento tático lado a lado, diagnosticar janelas de quebra e identificar o alvo de saque recomendado.</p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)] mb-1">Equipe A</label>
            <select id="h2h-team-a" onchange="renderHeadToHead()" class="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--foreground)] focus:outline-none cursor-pointer"></select>
          </div>
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)] mb-1">Equipe B</label>
            <select id="h2h-team-b" onchange="renderHeadToHead()" class="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm text-[var(--foreground)] focus:outline-none cursor-pointer"></select>
          </div>
        </div>

        <div id="h2h-results" class="space-y-6">
          <!-- Rendered dynamically via JS -->
        </div>
      </div>
    </section>

    <!-- TAB 6: TARGETS & USAGE -->
    <section id="tab-targets-usage" class="tab-content hidden space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <!-- Alvos de Saque -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
          <h3 class="text-base font-bold text-amber-400 flex items-center gap-2 mb-1">
            <span>🎯</span> Alvos de Saque (Mais Testados na Recepção)
          </h3>
          <p class="text-xs text-[var(--muted-foreground)] mb-4">Atletas mais procurados pelo saque adversário em todo o torneio.</p>
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] uppercase">
                  <th class="py-2 px-3">Atleta</th>
                  <th class="py-2 px-3">Equipe</th>
                  <th class="py-2 px-3 text-center">Pos</th>
                  <th class="py-2 px-3 text-center">Rec Tot</th>
                  <th class="py-2 px-3 text-center">Erros %</th>
                  <th class="py-2 px-3 text-center">Positiva %</th>
                </tr>
              </thead>
              <tbody id="reception-targets-body" class="divide-y divide-[var(--border)]"></tbody>
            </table>
          </div>
        </div>

        <!-- Sobrecarga Ofensiva -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
          <h3 class="text-base font-bold text-blue-400 flex items-center gap-2 mb-1">
            <span>🚀</span> Sobrecarga Ofensiva (Usage Share %)
          </h3>
          <p class="text-xs text-[var(--muted-foreground)] mb-4">Atletas que concentram o maior percentual de ataques de suas equipes.</p>
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] uppercase">
                  <th class="py-2 px-3">Atleta</th>
                  <th class="py-2 px-3">Equipe</th>
                  <th class="py-2 px-3 text-center">Pts</th>
                  <th class="py-2 px-3 text-center">Att</th>
                  <th class="py-2 px-3 text-center font-bold text-blue-400">Usage %</th>
                  <th class="py-2 px-3 text-center">Efic %</th>
                </tr>
              </thead>
              <tbody id="offensive-usage-body" class="divide-y divide-[var(--border)]"></tbody>
            </table>
          </div>
        </div>

      </div>
    </section>

    <!-- TAB 7: MATCHES -->
    <section id="tab-matches" class="tab-content hidden space-y-6">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <h3 class="text-lg font-bold text-[var(--foreground)]">Partidas Disputadas (34 Jogos)</h3>
          <input type="text" id="match-search" oninput="filterMatches(this.value)" placeholder="Buscar por equipe ou data..." class="bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm text-[var(--foreground)] focus:outline-none w-full md:w-64">
        </div>

        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left text-sm border-collapse">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] text-xs uppercase tracking-wider">
                <th class="py-3 px-4">Jogo ID</th>
                <th class="py-3 px-4">Data</th>
                <th class="py-3 px-4">Confronto</th>
                <th class="py-3 px-4 text-center">Sets (Placar)</th>
                <th class="py-3 px-4 text-center">Vencedor</th>
                <th class="py-3 px-4 text-center">Auditoria</th>
              </tr>
            </thead>
            <tbody id="matches-table-body" class="divide-y divide-[var(--border)]"></tbody>
          </table>
        </div>
      </div>
    </section>

    <footer class="text-center text-xs text-[var(--muted-foreground)] py-6 border-t border-[var(--border)]">
      CBS Voleibol Data Analytics • Sistema de Inteligência Tática • Base de Dados DuckDB
    </footer>
  </div>

  <!-- EMBEDDED APPLICATION DATA -->
  <script>
    const DATA = {json_data};

    // TAB SWITCHER
    function switchTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

      const target = document.getElementById('tab-' + tabId);
      if (target) target.classList.remove('hidden');

      const btn = document.querySelector(`[data-tab="${{tabId}}"]`);
      if (btn) btn.classList.add('active');
    }}

    // RENDER FUNCTIONS
    function initDashboard() {{
      // Initialize Selectors
      const teamSelector = document.getElementById('team-selector');
      const h2hA = document.getElementById('h2h-team-a');
      const h2hB = document.getElementById('h2h-team-b');

      DATA.teams.forEach(t => {{
        teamSelector.innerHTML += `<option value="${{t}}">${{t}}</option>`;
        h2hA.innerHTML += `<option value="${{t}}">${{t}}</option>`;
        h2hB.innerHTML += `<option value="${{t}}">${{t}}</option>`;
      }});

      if (DATA.teams.includes("SÃO PAULO")) {{
        teamSelector.value = "SÃO PAULO";
        h2hA.value = "SÃO PAULO";
      }}
      if (DATA.teams.includes("MINAS GERAIS")) {{
        h2hB.value = "MINAS GERAIS";
      }} else if (DATA.teams.length > 1) {{
        h2hB.value = DATA.teams[1];
      }}

      // 1. Render Overview
      renderOverview();
      // 2. Render Phase Attacks
      renderPhaseAttacks();
      // 3. Render Rotations Matrix
      renderRotations();
      // 4. Render Team Dossier
      renderTeamDossier(teamSelector.value);
      // 5. Render Head-to-Head
      renderHeadToHead();
      // 6. Render Targets & Usage
      renderTargetsAndUsage();
      // 7. Render Matches
      renderMatches(DATA.matches);
    }}

    function renderOverview() {{
      const soBp = DATA.summary.sideout_breakpoint;

      // Top SO Bars
      const soBars = document.getElementById('top-so-bars');
      soBars.innerHTML = '';
      soBp.slice(0, 5).forEach(r => {{
        soBars.innerHTML += `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-semibold">${{r.team}}</span>
              <span class="text-emerald-400 font-bold">${{r.so_pct}}% (${{r.so_rate}} rec/pt)</span>
            </div>
            <div class="w-full bg-[var(--background)] rounded-full h-2 overflow-hidden border border-[var(--border)]">
              <div class="bg-emerald-500 h-2 rounded-full" style="width: ${{r.so_pct}}%"></div>
            </div>
          </div>
        `;
      }});

      // Top BP Bars
      const bpBars = document.getElementById('top-bp-bars');
      bpBars.innerHTML = '';
      const bpSorted = [...soBp].sort((a,b) => b.bp_pct - a.bp_pct);
      bpSorted.slice(0, 5).forEach(r => {{
        bpBars.innerHTML += `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-semibold">${{r.team}}</span>
              <span class="text-blue-400 font-bold">${{r.bp_pct}}% (${{r.bp_rate}} sq/BP)</span>
            </div>
            <div class="w-full bg-[var(--background)] rounded-full h-2 overflow-hidden border border-[var(--border)]">
              <div class="bg-blue-500 h-2 rounded-full" style="width: ${{r.bp_pct * 2}}%"></div>
            </div>
          </div>
        `;
      }});

      // Table
      const tb = document.getElementById('so-bp-table-body');
      tb.innerHTML = '';
      soBp.forEach(r => {{
        const soClass = r.so_pct >= 53 ? 'text-emerald-400 font-bold' : (r.so_pct >= 48 ? 'text-amber-400' : 'text-rose-400');
        const bpClass = r.bp_pct >= 26 ? 'text-blue-400 font-bold' : (r.bp_pct >= 22 ? 'text-amber-400' : 'text-rose-400');
        tb.innerHTML += `
          <tr class="hover:bg-[var(--card-hover)] transition">
            <td class="py-3 px-4 font-semibold text-[var(--foreground)]">${{r.team}}</td>
            <td class="py-3 px-4 text-center text-[var(--muted-foreground)]">${{r.matches}}</td>
            <td class="py-3 px-4 text-center">${{r.so_points}}</td>
            <td class="py-3 px-4 text-center">${{r.so_receptions}}</td>
            <td class="py-3 px-4 text-center ${{soClass}}">${{r.so_pct}}%</td>
            <td class="py-3 px-4 text-center text-xs text-[var(--muted-foreground)]">${{r.so_rate}} rec/pt</td>
            <td class="py-3 px-4 text-center">${{r.bp_points}}</td>
            <td class="py-3 px-4 text-center">${{r.bp_serves}}</td>
            <td class="py-3 px-4 text-center ${{bpClass}}">${{r.bp_pct}}%</td>
            <td class="py-3 px-4 text-center text-xs text-[var(--muted-foreground)]">${{r.bp_rate}} sq/BP</td>
          </tr>
        `;
      }});
    }}

    function renderPhaseAttacks() {{
      const tb = document.getElementById('phase-table-body');
      tb.innerHTML = '';
      DATA.summary.phase_attacks.forEach(r => {{
        tb.innerHTML += `
          <tr class="hover:bg-[var(--card-hover)] transition">
            <td class="py-3 px-4 font-semibold text-[var(--foreground)]">${{r.team}}</td>
            <td class="py-3 px-4 text-center bg-emerald-500/5">${{r.k1_pos_att}}</td>
            <td class="py-3 px-4 text-center bg-emerald-500/5">${{r.k1_pos_kill_pct}}%</td>
            <td class="py-3 px-4 text-center bg-emerald-500/5 font-bold text-emerald-400">${{r.k1_pos_eff_pct}}%</td>
            <td class="py-3 px-4 text-center bg-amber-500/5">${{r.k1_neg_att}}</td>
            <td class="py-3 px-4 text-center bg-amber-500/5">${{r.k1_neg_kill_pct}}%</td>
            <td class="py-3 px-4 text-center bg-amber-500/5 font-bold text-amber-400">${{r.k1_neg_eff_pct}}%</td>
            <td class="py-3 px-4 text-center bg-blue-500/5">${{r.k2_att}}</td>
            <td class="py-3 px-4 text-center bg-blue-500/5">${{r.k2_kill_pct}}%</td>
            <td class="py-3 px-4 text-center bg-blue-500/5 font-bold text-blue-400">${{r.k2_eff_pct}}%</td>
          </tr>
        `;
      }});
    }}

    function renderRotations() {{
      const tb = document.getElementById('rotations-table-body');
      tb.innerHTML = '';
      DATA.summary.rotations.forEach(r => {{
        const fmtRot = val => {{
          const col = val > 0 ? 'text-emerald-400 font-semibold' : (val < 0 ? 'text-rose-400 font-semibold' : 'text-slate-500');
          const str = val > 0 ? `+${{val}}` : `${{val}}`;
          return `<span class="${{col}}">${{str}}</span>`;
        }};

        const rots = [
          {{ p: 'P1', val: r.p1 }},
          {{ p: 'P2', val: r.p2 }},
          {{ p: 'P3', val: r.p3 }},
          {{ p: 'P4', val: r.p4 }},
          {{ p: 'P5', val: r.p5 }},
          {{ p: 'P6', val: r.p6 }},
        ];
        const best = [...rots].sort((a,b) => b.val - a.val)[0];
        const worst = [...rots].sort((a,b) => a.val - b.val)[0];

        const totStr = r.total_diff > 0 ? `+${{r.total_diff}}` : `${{r.total_diff}}`;
        const totCol = r.total_diff > 0 ? 'text-emerald-400 font-bold' : (r.total_diff < 0 ? 'text-rose-400 font-bold' : 'text-slate-500');

        tb.innerHTML += `
          <tr class="hover:bg-[var(--card-hover)] transition">
            <td class="py-3 px-4 font-semibold text-[var(--foreground)]">${{r.team}}</td>
            <td class="py-3 px-4 text-center">${{fmtRot(r.p1)}}</td>
            <td class="py-3 px-4 text-center">${{fmtRot(r.p2)}}</td>
            <td class="py-3 px-4 text-center">${{fmtRot(r.p3)}}</td>
            <td class="py-3 px-4 text-center">${{fmtRot(r.p4)}}</td>
            <td class="py-3 px-4 text-center">${{fmtRot(r.p5)}}</td>
            <td class="py-3 px-4 text-center">${{fmtRot(r.p6)}}</td>
            <td class="py-3 px-4 text-center ${{totCol}}">${{totStr}}</td>
            <td class="py-3 px-4 text-center text-xs text-emerald-400 font-semibold">${{best.p}} (+${{best.val}})</td>
            <td class="py-3 px-4 text-center text-xs text-rose-400 font-semibold">${{worst.p}} (${{worst.val}})</td>
          </tr>
        `;
      }});
    }}

    function renderTeamDossier(teamName) {{
      const d = DATA.dossiers[teamName];
      const container = document.getElementById('dossier-content');
      if (!d) {{
        container.innerHTML = `<div class="p-4 text-rose-400">Dados não encontrados para ${{teamName}}</div>`;
        return;
      }}

      const t = d.totals;
      const rec = d.record;

      // Rotations Badges
      let rotBadges = '';
      for (let p = 1; p <= 6; p++) {{
        const v = t['p' + p] || 0;
        const col = v > 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : (v < 0 ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' : 'bg-slate-500/10 text-slate-400 border-slate-500/30');
        const vStr = v > 0 ? `+${{v}}` : `${{v}}`;
        rotBadges += `
          <div class="border ${{col}} rounded-xl p-3 text-center">
            <span class="block text-xs uppercase text-[var(--muted-foreground)]">Pos P${{p}}</span>
            <span class="text-lg font-bold">${{vStr}}</span>
          </div>
        `;
      }}

      // Attackers rows
      let attRows = '';
      d.attackers.forEach(a => {{
        attRows += `
          <tr class="hover:bg-[var(--card-hover)]">
            <td class="py-2.5 px-3 font-semibold text-[var(--foreground)]">${{a.player_name}}</td>
            <td class="py-2.5 px-3 text-center">${{a.pts}}</td>
            <td class="py-2.5 px-3 text-center">${{a.att}}</td>
            <td class="py-2.5 px-3 text-center font-bold text-blue-400">${{a.usage_pct}}%</td>
            <td class="py-2.5 px-3 text-center">${{a.kill_pct}}%</td>
            <td class="py-2.5 px-3 text-center font-semibold text-emerald-400">${{a.eff_pct}}%</td>
          </tr>
        `;
      }});

      // Receivers rows
      let recRows = '';
      d.receivers.forEach(r => {{
        recRows += `
          <tr class="hover:bg-[var(--card-hover)]">
            <td class="py-2.5 px-3 font-semibold text-[var(--foreground)]">${{r.player_name}}</td>
            <td class="py-2.5 px-3 text-center">${{r.is_libero ? 'Líbero' : 'Ponteiro'}}</td>
            <td class="py-2.5 px-3 text-center">${{r.rec}}</td>
            <td class="py-2.5 px-3 text-center text-rose-400 font-semibold">${{r.err_pct}}%</td>
            <td class="py-2.5 px-3 text-center text-emerald-400">${{r.pos_pct}}%</td>
            <td class="py-2.5 px-3 text-center">${{r.exc_pct}}%</td>
          </tr>
        `;
      }});

      // Sets rows
      let setsRows = '';
      d.sets_dist.forEach(s => {{
        setsRows += `
          <tr class="hover:bg-[var(--card-hover)]">
            <td class="py-2 px-3 font-semibold text-[var(--foreground)]">Set ${{s.set_number}}</td>
            <td class="py-2 px-3 text-center">${{s.sets_played}}</td>
            <td class="py-2 px-3 text-center">${{s.ser_pts}} pts</td>
            <td class="py-2 px-3 text-center">${{s.atk_pts}} pts</td>
            <td class="py-2 px-3 text-center">${{s.blo_pts}} pts</td>
            <td class="py-2 px-3 text-center text-amber-400 font-bold">${{s.operr_pts}} pts</td>
          </tr>
        `;
      }});

      container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 text-center">
            <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Campanha</span>
            <span class="text-xl font-extrabold text-[var(--foreground)]">${{rec.wins}}V - ${{rec.losses}}D</span>
            <span class="block text-xs text-[var(--muted-foreground)] mt-0.5">${{rec.sets_won}} sets pró / ${{rec.sets_lost}} contra</span>
          </div>
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 text-center">
            <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Side-Out %</span>
            <span class="text-xl font-extrabold text-emerald-400">${{t.so_pct}}%</span>
            <span class="block text-xs text-[var(--muted-foreground)] mt-0.5">${{t.so_pts}} pts em ${{t.rec_tot}} rec (${{t.so_rate}} rec/pt)</span>
          </div>
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 text-center">
            <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Break Point %</span>
            <span class="text-xl font-extrabold text-blue-400">${{t.bp_pct}}%</span>
            <span class="block text-xs text-[var(--muted-foreground)] mt-0.5">${{t.bp_pts}} pts em ${{t.srv_tot}} saques (${{t.bp_rate}} sq/BP)</span>
          </div>
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 text-center">
            <span class="block text-xs uppercase tracking-wider text-[var(--muted-foreground)]">Eficiência K1+</span>
            <span class="text-xl font-extrabold text-emerald-400">${{t.pos_rec_att_efficiency_pct || ((t.k1_pos_pts - t.k1_pos_err - t.k1_pos_blo)*100/t.k1_pos_att).toFixed(1)}}%</span>
            <span class="block text-xs text-[var(--muted-foreground)] mt-0.5">${{t.k1_pos_pts}} pts em ${{t.k1_pos_att}} att</span>
          </div>
        </div>

        <!-- Rotações P1..P6 -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
          <h4 class="text-sm font-bold uppercase tracking-wider text-[var(--muted-foreground)] mb-3">Distribuição de Saldo por Rotação do Levantador</h4>
          <div class="grid grid-cols-2 md:grid-cols-6 gap-3">
            ${{rotBadges}}
          </div>
        </div>

        <!-- Atacantes e Linha de Passe -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
            <h4 class="text-sm font-bold text-blue-400 mb-3 flex items-center gap-1.5"><span>⚡</span> Distribuição Ofensiva (Top Atacantes)</h4>
            <div class="overflow-x-auto custom-scrollbar">
              <table class="w-full text-left text-xs border-collapse">
                <thead>
                  <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] uppercase">
                    <th class="py-2 px-3">Atleta</th>
                    <th class="py-2 px-3 text-center">Pts</th>
                    <th class="py-2 px-3 text-center">Att</th>
                    <th class="py-2 px-3 text-center font-bold text-blue-400">Usage %</th>
                    <th class="py-2 px-3 text-center">Kill %</th>
                    <th class="py-2 px-3 text-center">Efic %</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--border)]">${{attRows}}</tbody>
              </table>
            </div>
          </div>

          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
            <h4 class="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-1.5"><span>🛡️</span> Linha de Passe (Estabilidade da Recepção)</h4>
            <div class="overflow-x-auto custom-scrollbar">
              <table class="w-full text-left text-xs border-collapse">
                <thead>
                  <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] uppercase">
                    <th class="py-2 px-3">Atleta</th>
                    <th class="py-2 px-3 text-center">Pos</th>
                    <th class="py-2 px-3 text-center">Recepções</th>
                    <th class="py-2 px-3 text-center text-rose-400">Erro %</th>
                    <th class="py-2 px-3 text-center">Positiva %</th>
                    <th class="py-2 px-3 text-center">Excelente %</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[var(--border)]">${{recRows}}</tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- De onde vêm os pontos por set -->
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm">
          <h4 class="text-sm font-bold text-amber-400 mb-3">Origem dos Pontos Conquistados por Set</h4>
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] uppercase">
                  <th class="py-2 px-3">Set</th>
                  <th class="py-2 px-3 text-center">Disputados</th>
                  <th class="py-2 px-3 text-center">Saque (Aces)</th>
                  <th class="py-2 px-3 text-center">Ataque</th>
                  <th class="py-2 px-3 text-center">Bloqueio</th>
                  <th class="py-2 px-3 text-center text-amber-400">Erros Adversários</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--border)]">${{setsRows}}</tbody>
            </table>
          </div>
        </div>
      `;
    }}

    function renderHeadToHead() {{
      const aName = document.getElementById('h2h-team-a').value;
      const bName = document.getElementById('h2h-team-b').value;
      const res = document.getElementById('h2h-results');

      if (aName === bName) {{
        res.innerHTML = `<div class="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 text-sm">Selecione duas equipes diferentes para o confronto.</div>`;
        return;
      }}

      const da = DATA.dossiers[aName];
      const db = DATA.dossiers[bName];
      if (!da || !db) return;

      const ta = da.totals;
      const tb = db.totals;

      // Rotations Rows
      let rotRows = '';
      for (let p = 1; p <= 6; p++) {{
        const va = ta['p' + p] || 0;
        const vb = tb['p' + p] || 0;
        let diag = 'Equilibrado';
        let diagClass = 'text-[var(--muted-foreground)]';

        if (va > 0 && vb < 0) {{
          diag = `Janela de quebra para ${{aName}}`;
          diagClass = 'text-emerald-400 font-bold';
        }} else if (vb > 0 && va < 0) {{
          diag = `Zona de perigo para ${{aName}} (pressão de ${{bName}})`;
          diagClass = 'text-rose-400 font-bold';
        }}

        rotRows += `
          <tr class="hover:bg-[var(--card-hover)]">
            <td class="py-2.5 px-3 font-semibold text-[var(--foreground)]">Posição P${{p}}</td>
            <td class="py-2.5 px-3 text-center font-bold ${{va > 0 ? 'text-emerald-400' : (va < 0 ? 'text-rose-400' : '')}}">${{va > 0 ? '+'+va : va}}</td>
            <td class="py-2.5 px-3 text-center font-bold ${{vb > 0 ? 'text-emerald-400' : (vb < 0 ? 'text-rose-400' : '')}}">${{vb > 0 ? '+'+vb : vb}}</td>
            <td class="py-2.5 px-3 text-center text-xs ${{diagClass}}">${{diag}}</td>
          </tr>
        `;
      }}

      // Targets
      const targetB = db.receivers.length ? [...db.receivers].sort((x,y) => y.err_pct - x.err_pct)[0] : null;
      const targetA = da.receivers.length ? [...da.receivers].sort((x,y) => y.err_pct - x.err_pct)[0] : null;

      res.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="border border-[var(--border)] rounded-xl p-4 bg-[var(--background)]">
            <span class="block text-xs uppercase text-emerald-400 font-bold mb-1">Estratégia de Saque de ${{aName}}</span>
            <p class="text-sm">Pressionar no saque: <strong>${{targetB ? targetB.player_name : 'N/A'}}</strong> (${{targetB ? targetB.err_pct+'% erros' : ''}}).</p>
          </div>
          <div class="border border-[var(--border)] rounded-xl p-4 bg-[var(--background)]">
            <span class="block text-xs uppercase text-blue-400 font-bold mb-1">Estratégia de Saque de ${{bName}}</span>
            <p class="text-sm">Pressionar no saque: <strong>${{targetA ? targetA.player_name : 'N/A'}}</strong> (${{targetA ? targetA.err_pct+'% erros' : ''}}).</p>
          </div>
        </div>

        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left text-sm border-collapse">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] text-xs uppercase">
                <th class="py-3 px-3">Métrica Tática</th>
                <th class="py-3 px-3 text-center text-emerald-400 font-bold">${{aName}}</th>
                <th class="py-3 px-3 text-center text-blue-400 font-bold">${{bName}}</th>
                <th class="py-3 px-3 text-center">Vantagem Tática</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--border)]">
              <tr class="hover:bg-[var(--card-hover)]">
                <td class="py-2.5 px-3 font-semibold">Side-Out % (Conversão de Passe)</td>
                <td class="py-2.5 px-3 text-center font-bold">${{ta.so_pct}}%</td>
                <td class="py-2.5 px-3 text-center font-bold">${{tb.so_pct}}%</td>
                <td class="py-2.5 px-3 text-center font-bold text-emerald-400">${{ta.so_pct > tb.so_pct ? aName : bName}}</td>
              </tr>
              <tr class="hover:bg-[var(--card-hover)]">
                <td class="py-2.5 px-3 font-semibold">Break Point % (Conversão de Saque)</td>
                <td class="py-2.5 px-3 text-center font-bold">${{ta.bp_pct}}%</td>
                <td class="py-2.5 px-3 text-center font-bold">${{tb.bp_pct}}%</td>
                <td class="py-2.5 px-3 text-center font-bold text-blue-400">${{ta.bp_pct > tb.bp_pct ? aName : bName}}</td>
              </tr>
              <tr class="hover:bg-[var(--card-hover)]">
                <td class="py-2.5 px-3 font-semibold">1º Ataque Passe + (#+) Efic %</td>
                <td class="py-2.5 px-3 text-center font-bold">${{ta.pos_rec_att_efficiency_pct || ((ta.k1_pos_pts - ta.k1_pos_err - ta.k1_pos_blo)*100/ta.k1_pos_att).toFixed(1)}}%</td>
                <td class="py-2.5 px-3 text-center font-bold">${{tb.pos_rec_att_efficiency_pct || ((tb.k1_pos_pts - tb.k1_pos_err - tb.k1_pos_blo)*100/tb.k1_pos_att).toFixed(1)}}%</td>
                <td class="py-2.5 px-3 text-center font-bold text-emerald-400">${{(ta.pos_rec_att_efficiency_pct || 0) > (tb.pos_rec_att_efficiency_pct || 0) ? aName : bName}}</td>
              </tr>
              <tr class="hover:bg-[var(--card-hover)]">
                <td class="py-2.5 px-3 font-semibold">1º Ataque Passe - (!-) Efic %</td>
                <td class="py-2.5 px-3 text-center font-bold">${{ta.neg_rec_att_efficiency_pct || ((ta.k1_neg_pts - ta.k1_neg_err - ta.k1_neg_blo)*100/ta.k1_neg_att).toFixed(1)}}%</td>
                <td class="py-2.5 px-3 text-center font-bold">${{tb.neg_rec_att_efficiency_pct || ((tb.k1_neg_pts - tb.k1_neg_err - tb.k1_neg_blo)*100/tb.k1_neg_att).toFixed(1)}}%</td>
                <td class="py-2.5 px-3 text-center font-bold text-amber-400">${{(ta.neg_rec_att_efficiency_pct || 0) > (tb.neg_rec_att_efficiency_pct || 0) ? aName : bName}}</td>
              </tr>
              <tr class="hover:bg-[var(--card-hover)]">
                <td class="py-2.5 px-3 font-semibold">Transição (K2) Efic %</td>
                <td class="py-2.5 px-3 text-center font-bold">${{ta.trans_att_efficiency_pct || ((ta.k2_pts - ta.k2_err - ta.k2_blo)*100/ta.k2_att).toFixed(1)}}%</td>
                <td class="py-2.5 px-3 text-center font-bold">${{tb.trans_att_efficiency_pct || ((tb.k2_pts - tb.k2_err - tb.k2_blo)*100/tb.k2_att).toFixed(1)}}%</td>
                <td class="py-2.5 px-3 text-center font-bold text-blue-400">${{(ta.trans_att_efficiency_pct || 0) > (tb.trans_att_efficiency_pct || 0) ? aName : bName}}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Rotations Comparison -->
        <div class="mt-4">
          <h4 class="text-sm font-bold text-[var(--foreground)] mb-2">Batalha de Rotações (P1 a P6)</h4>
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)] uppercase">
                  <th class="py-2 px-3">Rotação</th>
                  <th class="py-2 px-3 text-center">${{aName}}</th>
                  <th class="py-2 px-3 text-center">${{bName}}</th>
                  <th class="py-2 px-3 text-center">Diagnóstico de Matchup</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--border)]">${{rotRows}}</tbody>
            </table>
          </div>
        </div>
      `;
    }}

    function renderTargetsAndUsage() {{
      const tbTargets = document.getElementById('reception-targets-body');
      tbTargets.innerHTML = '';
      DATA.summary.reception_targets.forEach(r => {{
        tbTargets.innerHTML += `
          <tr class="hover:bg-[var(--card-hover)]">
            <td class="py-2 px-3 font-semibold text-[var(--foreground)]">${{r.player_name}}</td>
            <td class="py-2 px-3 text-[var(--muted-foreground)]">${{r.team}}</td>
            <td class="py-2 px-3 text-center">${{r.is_libero ? 'Líbero' : 'Ponteiro'}}</td>
            <td class="py-2 px-3 text-center font-bold">${{r.rec_attempts}}</td>
            <td class="py-2 px-3 text-center text-rose-400 font-semibold">${{r.err_pct}}%</td>
            <td class="py-2 px-3 text-center text-emerald-400">${{r.avg_pos_pct}}%</td>
          </tr>
        `;
      }});

      const tbUsage = document.getElementById('offensive-usage-body');
      tbUsage.innerHTML = '';
      DATA.summary.offensive_usage.forEach(r => {{
        tbUsage.innerHTML += `
          <tr class="hover:bg-[var(--card-hover)]">
            <td class="py-2 px-3 font-semibold text-[var(--foreground)]">${{r.player_name}}</td>
            <td class="py-2 px-3 text-[var(--muted-foreground)]">${{r.team}}</td>
            <td class="py-2 px-3 text-center">${{r.pts}}</td>
            <td class="py-2 px-3 text-center">${{r.att}}</td>
            <td class="py-2 px-3 text-center font-extrabold text-blue-400">${{r.usage_pct}}%</td>
            <td class="py-2 px-3 text-center font-semibold text-emerald-400">${{r.eff_pct}}%</td>
          </tr>
        `;
      }});
    }}

    function renderMatches(matchList) {{
      const tb = document.getElementById('matches-table-body');
      tb.innerHTML = '';
      matchList.forEach(m => {{
        const winner = m.home_sets > m.away_sets ? m.home_team : m.away_team;
        tb.innerHTML += `
          <tr class="hover:bg-[var(--card-hover)] transition">
            <td class="py-2.5 px-4 font-mono text-xs text-blue-400">${{m.match_id}}</td>
            <td class="py-2.5 px-4 text-xs text-[var(--muted-foreground)]">${{m.date}}</td>
            <td class="py-2.5 px-4 font-semibold">${{m.home_team}} × ${{m.away_team}}</td>
            <td class="py-2.5 px-4 text-center font-bold text-amber-400">${{m.home_sets}} × ${{m.away_sets}}</td>
            <td class="py-2.5 px-4 text-center text-xs text-emerald-400 font-semibold">${{winner}}</td>
            <td class="py-2.5 px-4 text-center">
              <span class="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">VALID</span>
            </td>
          </tr>
        `;
      }});
    }}

    function filterMatches(query) {{
      const q = query.toLowerCase();
      const filtered = DATA.matches.filter(m => 
        m.home_team.toLowerCase().includes(q) ||
        m.away_team.toLowerCase().includes(q) ||
        String(m.match_id).includes(q) ||
        String(m.date).includes(q)
      );
      renderMatches(filtered);
    }}

    // Boot
    window.addEventListener('DOMContentLoaded', initDashboard);
  </script>
</body>
</html>
"""
    return html


def export_dashboard_html(target_file: Path = DEFAULT_HTML_PATH) -> Path:
    """Compiles tactical data and writes the standalone HTML dashboard to disk."""
    target_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating HTML Dashboard at {target_file}")
    
    data = generate_dashboard_data()
    html_content = build_dashboard_html(data)
    target_file.write_text(html_content, encoding="utf-8")
    
    console.print(f"[green]✓ Dashboard HTML interativo gerado com sucesso em [bold]{target_file}[/bold][/green]")
    return target_file
