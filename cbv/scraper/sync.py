"""Daily synchronization and CT bulletin generator for in-progress CBS tournaments."""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import webbrowser
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cbv.config import logger, BASE_DIR
from cbv.scraper.competition import scrape_competition, parse_competition_url
from cbv.database.repository import default_repo
from cbv.export.html_dashboard import export_dashboard_html
from cbv.export.csv_export import export_all_to_csv
from cbv.export.json_export import export_all_to_json
from cbv.analysis.setter_distribution import compute_setter_distribution

console = Console()
EXPORTS_DIR = BASE_DIR / "exports"


def generate_ct_bulletin_files(
    comp_title: str,
    total_in_db: int,
    new_matches_count: int,
    recent_matches: List[Dict[str, Any]],
    standings: List[Dict[str, Any]],
    top_scorers: List[Dict[str, Any]],
    top_blockers: List[Dict[str, Any]],
    top_servers: List[Dict[str, Any]],
    top_receivers: List[Dict[str, Any]],
    tactical_alerts: List[str],
    dashboard_path: Optional[Path],
) -> Tuple[Path, Path]:
    """Generates formatted TXT and MD bulletins for CT distribution (WhatsApp / email)."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = EXPORTS_DIR / "boletim_ct_diario.txt"
    md_path = EXPORTS_DIR / "boletim_ct_diario.md"
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 1. Plain text format (ideal for WhatsApp / telegram messages)
    lines_txt = []
    lines_txt.append(f"🏐 *BOLETIM DIÁRIO DA COMISSÃO TÉCNICA (CT)* 🏐")
    lines_txt.append(f"🏆 *Competição:* {comp_title}")
    lines_txt.append(f"📅 *Atualização:* {now_str}")
    lines_txt.append("=" * 45)
    lines_txt.append(f"📊 *STATUS DA BASE DE DADOS:*")
    lines_txt.append(f"• Total de jogos auditados: {total_in_db}")
    if new_matches_count > 0:
        lines_txt.append(f"• Jogos novos inseridos hoje: {new_matches_count}")
    else:
        lines_txt.append("• Base 100% atualizada (sem jogos pendentes hoje)")

    if recent_matches:
        lines_txt.append("\n📌 *ÚLTIMOS RESULTADOS CADASTRADOS:*")
        for m in recent_matches[:5]:
            lines_txt.append(f"• {m['home_team']} {m['home_sets']} x {m['away_sets']} {m['away_team']} (Jogo {m['match_id']})")

    if standings:
        lines_txt.append("\n📈 *CLASSIFICAÇÃO GERAL ESTIMADA:*")
        lines_txt.append("Pos | Equipe | J | V | D | Sets Pró/Contra")
        for idx, s in enumerate(standings[:8], start=1):
            lines_txt.append(f"{idx:02d}º | {s['team']} | {int(s['games'])}J | {int(s['wins'])}V-{int(s['losses'])}D | {int(s['sets_won'])}:{int(s['sets_lost'])}")

    if top_scorers:
        lines_txt.append("\n🔥 *TOP PONTUADORAS:*")
        for idx, p in enumerate(top_scorers[:5], start=1):
            lines_txt.append(f"{idx}. {p['player_name']} ({p['team']}) — {int(p['pts'])} pts ({int(p['att'])} ataques, {p['kill_pct']}%)")

    if top_blockers:
        lines_txt.append("\n🧱 *TOP BLOQUEADORAS:*")
        for idx, p in enumerate(top_blockers[:5], start=1):
            lines_txt.append(f"{idx}. {p['player_name']} ({p['team']}) — {int(p['blk'])} pontos de bloqueio")

    if top_servers:
        lines_txt.append("\n🎯 *TOP SACADORAS (ACES):*")
        for idx, p in enumerate(top_servers[:5], start=1):
            lines_txt.append(f"{idx}. {p['player_name']} ({p['team']}) — {int(p['aces'])} aces")

    if top_receivers:
        lines_txt.append("\n🛡️ *SEGURANÇA NA RECEPÇÃO (PASSE A/B):*")
        for idx, p in enumerate(top_receivers[:5], start=1):
            lines_txt.append(f"{idx}. {p['player_name']} ({p['team']}) — {p['pos_pct']}% positivo ({p['exc_pct']}% excelente em {int(p['rec'])} rec)")

    if tactical_alerts:
        lines_txt.append("\n🧠 *ALERTAS TÁTICOS & TENDÊNCIAS DE DISTRIBUIÇÃO:*")
        for alert in tactical_alerts:
            lines_txt.append(f"• {alert}")

    if dashboard_path:
        lines_txt.append("\n💻 *DASHBOARD INTERATIVO COMPLETO:*")
        lines_txt.append(f"{dashboard_path.resolve().as_uri()}")

    txt_content = "\n".join(lines_txt)
    txt_path.write_text(txt_content, encoding="utf-8")

    # 2. Markdown format
    lines_md = []
    lines_md.append(f"# Boletim Diário da Comissão Técnica (CT)")
    lines_md.append(f"**Competição:** {comp_title}  ")
    lines_md.append(f"**Data da Atualização:** {now_str}  ")
    lines_md.append(f"**Status da Base:** {total_in_db} jogos auditados ({new_matches_count} novos hoje)\n")

    if recent_matches:
        lines_md.append("## Últimos Resultados")
        for m in recent_matches[:5]:
            lines_md.append(f"- **{m['home_team']}** {m['home_sets']} × {m['away_sets']} **{m['away_team']}** *(Jogo {m['match_id']})*")
        lines_md.append("")

    if standings:
        lines_md.append("## Classificação Estimada")
        lines_md.append("| Pos | Equipe | Jogos | V | D | Sets Vencidos | Sets Perdidos |")
        lines_md.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|")
        for idx, s in enumerate(standings, start=1):
            lines_md.append(f"| {idx} | {s['team']} | {int(s['games'])} | {int(s['wins'])} | {int(s['losses'])} | {int(s['sets_won'])} | {int(s['sets_lost'])} |")
        lines_md.append("")

    if top_scorers:
        lines_md.append("## Destaques Individuais")
        lines_md.append("### Top Pontuadoras")
        for idx, p in enumerate(top_scorers[:5], start=1):
            lines_md.append(f"{idx}. **{p['player_name']}** ({p['team']}): {int(p['pts'])} pts ({int(p['att'])} ataques, {p['kill_pct']}%)")
        lines_md.append("")

    if tactical_alerts:
        lines_md.append("## Inteligência Tática e Previsões")
        for alert in tactical_alerts:
            lines_md.append(f"- {alert}")
        lines_md.append("")

    if dashboard_path:
        lines_md.append(f"> Dashboard HTML disponível em: `{dashboard_path.resolve()}`")

    md_content = "\n".join(lines_md)
    md_path.write_text(md_content, encoding="utf-8")

    return txt_path, md_path


def run_daily_sync(
    competition: str = "cbs",
    category: str = "sub18",
    gender: str = "feminino",
    division: str = "especial",
    season: int = 2026,
    open_browser: bool = True,
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the complete daily sync pipeline for ongoing championships:
    1. Polites scrape of the CBV portal for today's new matches (via URL or parameters)
    2. Incremental ingestion into DuckDB (zero duplicate rows)
    3. Regeneration of standalone HTML dashboard and CSV/JSON exports
    4. Generation of Daily CT Bulletin (saved in TXT and MD, plus terminal rendering)
    """
    if url:
        parsed = parse_competition_url(url)
        competition = parsed["competition"]
        category = parsed["category"]
        gender = parsed["gender"]
        division = parsed["division"]
        season = parsed["season"]

    comp_title = f"{competition.upper()} {category.upper()} {gender.upper()} {division.upper()} {season}"
    console.print(Panel(
        f"[bold yellow]SINCRONIZAÇÃO DIÁRIA — {comp_title}[/bold yellow]\n"
        f"[dim]Buscando atualizações de partidas e súmulas no portal oficial da CBV[/dim]",
        expand=False,
    ))

    # 1. Scrape incremental
    scrape_res = scrape_competition(
        competition=competition,
        category=category,
        gender=gender,
        division=division,
        season=season,
        force=False,
        url=url,
    )

    new_matches_count = scrape_res.get("valid", 0) + scrape_res.get("warning", 0)

    # 2. Update Exports and Dashboard if new matches entered or base exists
    html_path = None
    if new_matches_count > 0 or scrape_res.get("total", 0) > 0:
        console.print("\n[bold cyan]Atualizando Dashboard e Exportações para a Comissão Técnica...[/bold cyan]")
        html_path = export_dashboard_html()
        export_all_to_csv()
        export_all_to_json()

    # 3. Query Database for CT Bulletin
    with default_repo.get_connection() as conn:
        total_in_db = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]

        recent_matches = conn.execute("""
            SELECT match_id, home_team, away_team, home_sets, away_sets, date 
            FROM matches 
            ORDER BY date DESC, match_id DESC 
            LIMIT 5
        """).fetchdf().to_dict(orient="records")

        # Standings
        standings_df = conn.execute("""
            WITH team_matches AS (
                SELECT home_team AS team, 
                       CASE WHEN home_sets > away_sets THEN 1 ELSE 0 END AS win,
                       CASE WHEN home_sets < away_sets THEN 1 ELSE 0 END AS loss,
                       home_sets AS sw, away_sets AS sl
                FROM matches WHERE home_sets IS NOT NULL
                UNION ALL
                SELECT away_team AS team, 
                       CASE WHEN away_sets > home_sets THEN 1 ELSE 0 END AS win,
                       CASE WHEN away_sets < home_sets THEN 1 ELSE 0 END AS loss,
                       away_sets AS sw, home_sets AS sl
                FROM matches WHERE away_sets IS NOT NULL
            )
            SELECT team, 
                   COUNT(*) AS games,
                   SUM(win) AS wins,
                   SUM(loss) AS losses,
                   SUM(sw) AS sets_won,
                   SUM(sl) AS sets_lost,
                   (SUM(win) * 3) AS points_est
            FROM team_matches
            GROUP BY team
            ORDER BY wins DESC, sets_won DESC
        """).fetchdf()
        standings = standings_df.to_dict(orient="records") if not standings_df.empty else []

        # Top scorers
        scorers_df = conn.execute("""
            SELECT player_name, team, 
                   SUM(points_total) as pts,
                   SUM(attack_attempts) as att,
                   ROUND(SUM(attack_points) * 100.0 / NULLIF(SUM(attack_attempts), 0), 1) as kill_pct
            FROM player_match_stats
            WHERE points_total IS NOT NULL
            GROUP BY player_name, team
            ORDER BY pts DESC
            LIMIT 5
        """).fetchdf()
        top_scorers = scorers_df.to_dict(orient="records") if not scorers_df.empty else []

        # Top blockers
        blockers_df = conn.execute("""
            SELECT player_name, team, SUM(block_points) as blk
            FROM player_match_stats
            WHERE block_points IS NOT NULL
            GROUP BY player_name, team
            ORDER BY blk DESC
            LIMIT 5
        """).fetchdf()
        top_blockers = blockers_df.to_dict(orient="records") if not blockers_df.empty else []

        # Top servers
        servers_df = conn.execute("""
            SELECT player_name, team, SUM(serve_points) as aces
            FROM player_match_stats
            WHERE serve_points IS NOT NULL
            GROUP BY player_name, team
            ORDER BY aces DESC
            LIMIT 5
        """).fetchdf()
        top_servers = servers_df.to_dict(orient="records") if not servers_df.empty else []

        # Top receivers
        receivers_df = conn.execute("""
            SELECT player_name, team, 
                   SUM(reception_attempts) as rec,
                   ROUND(AVG(reception_positive_pct), 1) as pos_pct,
                   ROUND(AVG(reception_excellent_pct), 1) as exc_pct
            FROM player_match_stats
            WHERE reception_attempts IS NOT NULL
            GROUP BY player_name, team
            HAVING SUM(reception_attempts) >= 15
            ORDER BY pos_pct DESC
            LIMIT 5
        """).fetchdf()
        top_receivers = receivers_df.to_dict(orient="records") if not receivers_df.empty else []

    # 4. Generate Tactical Distribution Alerts for top teams
    tactical_alerts: List[str] = []
    top_teams = [s["team"] for s in standings[:3]]
    for t in top_teams:
        try:
            dist_pos = compute_setter_distribution(t, rotation="P1", pass_quality="positive")
            dist_neg = compute_setter_distribution(t, rotation="P1", pass_quality="negative")
            if dist_pos and dist_neg and dist_neg["distribution"]:
                main_target = dist_neg["distribution"][0]
                tactical_alerts.append(
                    f"**{t} (P1)**: Com passe quebrado (-!), a levantadora joga {main_target['probability_pct']}% "
                    f"das bolas em {main_target['player_name']} ({main_target['zone']}). Bloqueio duplo antecipado."
                )
        except Exception:
            pass

    # 5. Write Files
    txt_path, md_path = generate_ct_bulletin_files(
        comp_title=comp_title,
        total_in_db=total_in_db,
        new_matches_count=new_matches_count,
        recent_matches=recent_matches,
        standings=standings,
        top_scorers=top_scorers,
        top_blockers=top_blockers,
        top_servers=top_servers,
        top_receivers=top_receivers,
        tactical_alerts=tactical_alerts,
        dashboard_path=html_path,
    )

    # 6. Render Terminal Summary
    console.print("\n" + "=" * 60)
    console.print(Panel(
        f"[bold green]BOLETIM DIÁRIO PARA A COMISSÃO TÉCNICA (CT)[/bold green]\n"
        f"[dim]Gerado automaticamente para compartilhamento e tomada de decisão[/dim]",
        expand=False,
    ))

    console.print(f"• [bold]Status Geral do Torneio:[/bold] {total_in_db} partidas auditadas no banco.")
    if new_matches_count > 0:
        console.print(f"• [bold green]Novas Partidas Ingeridas Hoje:[/bold green] {new_matches_count} jogos processados.")
    else:
        console.print("• [dim]Nenhuma partida nova publicada hoje até o momento. Base 100% atualizada.[/dim]")

    if recent_matches:
        console.print("\n[bold]Últimos Resultados Auditados:[/bold]")
        for m in recent_matches[:4]:
            console.print(f"  • {m['home_team']} {m['home_sets']} × {m['away_sets']} {m['away_team']} (Jogo {m['match_id']})")

    if standings:
        console.print("\n[bold cyan]Classificação Geral Estimada:[/bold cyan]")
        st_tbl = Table(show_header=True, header_style="bold magenta")
        st_tbl.add_column("Pos", justify="center")
        st_tbl.add_column("Equipe")
        st_tbl.add_column("J", justify="center")
        st_tbl.add_column("V", justify="center")
        st_tbl.add_column("D", justify="center")
        st_tbl.add_column("Sets V-P", justify="center")

        for idx, s in enumerate(standings[:6], start=1):
            st_tbl.add_row(
                f"{idx:02d}º",
                s["team"],
                str(s["games"]),
                str(s["wins"]),
                str(s["losses"]),
                f"{s['sets_won']} - {s['sets_lost']}",
            )
        console.print(st_tbl)

    if tactical_alerts:
        console.print("\n[bold yellow]Alertas Táticos da CT (Tendências de Levantamento):[/bold yellow]")
        for alert in tactical_alerts:
            console.print(f"  • {alert}")

    console.print(f"\n[bold green]✓ Boletim gerado para compartilhamento:[/bold green]")
    console.print(f"  • Texto simples (WhatsApp): [underline]{txt_path.resolve()}[/underline]")
    console.print(f"  • Relatório Markdown: [underline]{md_path.resolve()}[/underline]")

    if html_path and html_path.exists():
        console.print(f"  • Dashboard HTML: [underline]{html_path.resolve()}[/underline]")
        if open_browser:
            console.print("[dim]Abrindo no navegador...[/dim]")
            webbrowser.open(html_path.resolve().as_uri())

    console.print("=" * 60 + "\n")

    return {
        "competition": comp_title,
        "new_matches": new_matches_count,
        "total_matches": total_in_db,
        "dashboard_path": str(html_path) if html_path else None,
        "bulletin_txt_path": str(txt_path),
        "bulletin_md_path": str(md_path),
    }
