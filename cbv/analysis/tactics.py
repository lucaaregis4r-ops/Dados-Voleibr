"""Tactical analysis and match intelligence reporting engine."""

from typing import Optional, Dict, Any, List
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cbv.database.repository import default_repo

console = Console()


def get_match_tactical_report(match_id: int) -> Optional[Dict[str, Any]]:
    """Fetches complete tactical metrics from DuckDB for a specific match."""
    with default_repo.get_connection() as conn:
        match_info = conn.execute(
            "SELECT home_team, away_team, home_sets, away_sets, date FROM matches WHERE match_id = ?",
            [match_id],
        ).fetchone()
        if not match_info:
            return None

        teams_df = conn.execute(
            "SELECT * FROM team_tactical_stats WHERE match_id = ?",
            [match_id],
        ).fetchdf()

        sets_df = conn.execute(
            "SELECT * FROM set_tactical_stats WHERE match_id = ? ORDER BY set_number, team",
            [match_id],
        ).fetchdf()

        players_df = conn.execute(
            """
            SELECT player_name, team, is_libero, points_total, attack_attempts, attack_points, 
                   reception_attempts, serve_points, block_points
            FROM player_match_stats 
            WHERE match_id = ?
            ORDER BY team, points_total DESC
            """,
            [match_id],
        ).fetchdf()

    return {
        "match_id": match_id,
        "home_team": match_info[0],
        "away_team": match_info[1],
        "home_sets": match_info[2],
        "away_sets": match_info[3],
        "date": str(match_info[4]),
        "teams": teams_df.to_dict(orient="records"),
        "sets": sets_df.to_dict(orient="records"),
        "players": players_df.to_dict(orient="records"),
    }


def display_match_tactics(match_id: int) -> None:
    """Renders formatted tactical intelligence report for a single match."""
    data = get_match_tactical_report(match_id)
    if not data:
        console.print(f"[red]Partida {match_id} não encontrada no banco DuckDB.[/red]")
        return

    home = data["home_team"]
    away = data["away_team"]
    title = f"RELATÓRIO TÁTICO — JOGO {match_id}: {home} {data['home_sets']} × {data['away_sets']} {away}"
    console.print(Panel(f"[bold yellow]{title}[/bold yellow]\n[dim]Data: {data['date']}[/dim]", expand=False))

    teams = {t["team"]: t for t in data["teams"]}
    t_home = teams.get(home)
    t_away = teams.get(away)

    if not t_home or not t_away:
        console.print("[yellow]Dados táticos detalhados não disponíveis para esta partida.[/yellow]")
        return

    # 1. SIDE-OUT & BREAK POINT
    console.print("\n[bold cyan]1. EFICIÊNCIA DE FASE: SIDE-OUT (SO) vs BREAK POINT (BP)[/bold cyan]")
    so_table = Table(show_header=True, header_style="bold magenta")
    so_table.add_column("Métrica Tática", style="dim")
    so_table.add_column(home, justify="center")
    so_table.add_column(away, justify="center")

    so_table.add_row(
        "Pontos de Side-Out (K1)",
        f"{t_home['sideout_points']} pts",
        f"{t_away['sideout_points']} pts",
    )
    so_table.add_row(
        "Volume de Recepções",
        f"{t_home['sideout_receptions']} recepções",
        f"{t_away['sideout_receptions']} recepções",
    )
    h_so_rate = f"{t_home['sideout_rate']:.2f} rec = 1 pt" if t_home['sideout_rate'] else "N/A"
    a_so_rate = f"{t_away['sideout_rate']:.2f} rec = 1 pt" if t_away['sideout_rate'] else "N/A"
    so_table.add_row("Taxa de Side-Out (Recepções/Ponto)", h_so_rate, a_so_rate)

    so_table.add_row(
        "Pontos de Break Point (K2)",
        f"{t_home['breakpoint_points']} pts",
        f"{t_away['breakpoint_points']} pts",
    )
    so_table.add_row(
        "Volume de Saques",
        f"{t_home['breakpoint_serves']} saques",
        f"{t_away['breakpoint_serves']} saques",
    )
    h_bp_rate = f"{t_home['breakpoint_rate']:.2f} sq = 1 BP" if t_home['breakpoint_rate'] else "N/A"
    a_bp_rate = f"{t_away['breakpoint_rate']:.2f} sq = 1 BP" if t_away['breakpoint_rate'] else "N/A"
    so_table.add_row("Taxa de Break Point (Saques/BP)", h_bp_rate, a_bp_rate)
    console.print(so_table)

    # 2. ATAQUE POR FASE
    console.print("\n[bold cyan]2. ATAQUE POR SITUAÇÃO DE RECEPÇÃO & TRANSIÇÃO[/bold cyan]")
    att_table = Table(show_header=True, header_style="bold magenta")
    att_table.add_column("Fase Ofensiva")
    att_table.add_column(f"{home} (Att | Pts% | Blo | Err | Efic%)", justify="center")
    att_table.add_column(f"{away} (Att | Pts% | Blo | Err | Efic%)", justify="center")

    # K1 Positive
    att_table.add_row(
        "1º Ataque c/ Passe + (#+)",
        f"{t_home['pos_rec_att_attempts']} att | [bold green]{t_home['pos_rec_att_points_pct']}%[/bold green] | {t_home['pos_rec_att_blocked']}b | {t_home['pos_rec_att_errors']}e | {t_home['pos_rec_att_efficiency_pct']}%",
        f"{t_away['pos_rec_att_attempts']} att | [bold green]{t_away['pos_rec_att_points_pct']}%[/bold green] | {t_away['pos_rec_att_blocked']}b | {t_away['pos_rec_att_errors']}e | {t_away['pos_rec_att_efficiency_pct']}%",
    )
    # K1 Negative
    att_table.add_row(
        "1º Ataque c/ Passe - (!-)",
        f"{t_home['neg_rec_att_attempts']} att | [bold yellow]{t_home['neg_rec_att_points_pct']}%[/bold yellow] | {t_home['neg_rec_att_blocked']}b | {t_home['neg_rec_att_errors']}e | {t_home['neg_rec_att_efficiency_pct']}%",
        f"{t_away['neg_rec_att_attempts']} att | [bold yellow]{t_away['neg_rec_att_points_pct']}%[/bold yellow] | {t_away['neg_rec_att_blocked']}b | {t_away['neg_rec_att_errors']}e | {t_away['neg_rec_att_efficiency_pct']}%",
    )
    # K2 Transition
    att_table.add_row(
        "Transição / Contra-Ataque",
        f"{t_home['trans_att_attempts']} att | [bold cyan]{t_home['trans_att_points_pct']}%[/bold cyan] | {t_home['trans_att_blocked']}b | {t_home['trans_att_errors']}e | {t_home['trans_att_efficiency_pct']}%",
        f"{t_away['trans_att_attempts']} att | [bold cyan]{t_away['trans_att_points_pct']}%[/bold cyan] | {t_away['trans_att_blocked']}b | {t_away['trans_att_errors']}e | {t_away['trans_att_efficiency_pct']}%",
    )
    console.print(att_table)

    # 3. MAPEAMENTO DE ROTAÇÕES (P1 a P6)
    console.print("\n[bold cyan]3. MAPEAMENTO DE ROTAÇÕES DO LEVANTADOR (SALDO DE PONTOS)[/bold cyan]")
    rot_table = Table(show_header=True, header_style="bold magenta")
    rot_table.add_column("Rotação")
    rot_table.add_column(f"{home} (Saldo)", justify="center")
    rot_table.add_column(f"{away} (Saldo)", justify="center")

    for p in range(1, 7):
        h_diff = t_home.get(f"p{p}_diff", 0) or 0
        a_diff = t_away.get(f"p{p}_diff", 0) or 0
        h_str = f"+{h_diff}" if h_diff > 0 else str(h_diff)
        a_str = f"+{a_diff}" if a_diff > 0 else str(a_diff)
        h_style = "green" if h_diff > 0 else ("red" if h_diff < 0 else "dim")
        a_style = "green" if a_diff > 0 else ("red" if a_diff < 0 else "dim")
        rot_table.add_row(f"P{p} (Levantador na pos {p})", f"[{h_style}]{h_str}[/{h_style}]", f"[{a_style}]{a_str}[/{a_style}]")
    console.print(rot_table)

    # Destaques de rotação
    h_best = max(range(1, 7), key=lambda p: t_home.get(f"p{p}_diff", 0) or 0)
    h_worst = min(range(1, 7), key=lambda p: t_home.get(f"p{p}_diff", 0) or 0)
    a_best = max(range(1, 7), key=lambda p: t_away.get(f"p{p}_diff", 0) or 0)
    a_worst = min(range(1, 7), key=lambda p: t_away.get(f"p{p}_diff", 0) or 0)

    console.print(f"[dim]• {home}: Rotação mais forte: [bold green]P{h_best} (+{t_home.get(f'p{h_best}_diff', 0)})[/bold green] | Mais vulnerável: [bold red]P{h_worst} ({t_home.get(f'p{h_worst}_diff', 0)})[/bold red][/dim]")
    console.print(f"[dim]• {away}: Rotação mais forte: [bold green]P{a_best} (+{t_away.get(f'p{a_best}_diff', 0)})[/bold green] | Mais vulnerável: [bold red]P{a_worst} ({t_away.get(f'p{a_worst}_diff', 0)})[/bold red][/dim]")

    # 4. CARGA TÁTICA INDIVIDUAL (USO OFENSIVO E SUSTENTAÇÃO DE PASSE)
    console.print("\n[bold cyan]4. CARGA TÁTICA INDIVIDUAL (USAGE SHARE)[/bold cyan]")
    total_home_att = sum(p["attack_attempts"] or 0 for p in data["players"] if p["team"] == home)
    total_away_att = sum(p["attack_attempts"] or 0 for p in data["players"] if p["team"] == away)
    total_home_rec = sum(p["reception_attempts"] or 0 for p in data["players"] if p["team"] == home)
    total_away_rec = sum(p["reception_attempts"] or 0 for p in data["players"] if p["team"] == away)

    load_table = Table(show_header=True, header_style="bold magenta")
    load_table.add_column("Atleta")
    load_table.add_column("Equipe")
    load_table.add_column("Pts", justify="center")
    load_table.add_column("Ataque (Vol / Usage %)", justify="center")
    load_table.add_column("Passe (Vol / Share %)", justify="center")

    for p in data["players"][:8]:
        team_att = total_home_att if p["team"] == home else total_away_att
        team_rec = total_home_rec if p["team"] == home else total_away_rec
        att_vol = p["attack_attempts"] or 0
        rec_vol = p["reception_attempts"] or 0
        att_share = (att_vol / team_att * 100) if team_att > 0 else 0.0
        rec_share = (rec_vol / team_rec * 100) if team_rec > 0 else 0.0

        load_table.add_row(
            p["player_name"],
            p["team"],
            str(p["points_total"] or 0),
            f"{att_vol} att ({att_share:.1f}%)",
            f"{rec_vol} rec ({rec_share:.1f}%)",
        )
    console.print(load_table)
    console.print()


def get_competition_tactical_summary() -> Dict[str, pd.DataFrame]:
    """Generates complete aggregated tactical intelligence across all competition matches."""
    with default_repo.get_connection() as conn:
        # 1. SO and BP
        so_bp_df = conn.execute("""
            SELECT 
                team,
                COUNT(*) as matches,
                CAST(SUM(sideout_points) AS INT) as so_points,
                CAST(SUM(sideout_receptions) AS INT) as so_receptions,
                ROUND(SUM(sideout_points) * 100.0 / NULLIF(SUM(sideout_receptions), 0), 1) as so_pct,
                ROUND(SUM(sideout_receptions) * 1.0 / NULLIF(SUM(sideout_points), 0), 2) as so_rate,
                CAST(SUM(breakpoint_points) AS INT) as bp_points,
                CAST(SUM(breakpoint_serves) AS INT) as bp_serves,
                ROUND(SUM(breakpoint_points) * 100.0 / NULLIF(SUM(breakpoint_serves), 0), 1) as bp_pct,
                ROUND(SUM(breakpoint_serves) * 1.0 / NULLIF(SUM(breakpoint_points), 0), 2) as bp_rate
            FROM team_tactical_stats
            GROUP BY team
            ORDER BY so_pct DESC
        """).fetchdf()

        # 2. Phase Attacks
        phase_df = conn.execute("""
            SELECT 
                team,
                CAST(SUM(pos_rec_att_attempts) AS INT) as k1_pos_att,
                ROUND(SUM(pos_rec_att_points) * 100.0 / NULLIF(SUM(pos_rec_att_attempts), 0), 1) as k1_pos_kill_pct,
                ROUND((SUM(pos_rec_att_points) - SUM(pos_rec_att_errors) - SUM(pos_rec_att_blocked)) * 100.0 / NULLIF(SUM(pos_rec_att_attempts), 0), 1) as k1_pos_eff_pct,
                CAST(SUM(neg_rec_att_attempts) AS INT) as k1_neg_att,
                ROUND(SUM(neg_rec_att_points) * 100.0 / NULLIF(SUM(neg_rec_att_attempts), 0), 1) as k1_neg_kill_pct,
                ROUND((SUM(neg_rec_att_points) - SUM(neg_rec_att_errors) - SUM(neg_rec_att_blocked)) * 100.0 / NULLIF(SUM(neg_rec_att_attempts), 0), 1) as k1_neg_eff_pct,
                CAST(SUM(trans_att_attempts) AS INT) as k2_att,
                ROUND(SUM(trans_att_points) * 100.0 / NULLIF(SUM(trans_att_attempts), 0), 1) as k2_kill_pct,
                ROUND((SUM(trans_att_points) - SUM(trans_att_errors) - SUM(trans_att_blocked)) * 100.0 / NULLIF(SUM(trans_att_attempts), 0), 1) as k2_eff_pct
            FROM team_tactical_stats
            GROUP BY team
            ORDER BY k1_pos_eff_pct DESC
        """).fetchdf()

        # 3. Rotations Matrix
        rot_df = conn.execute("""
            SELECT 
                team,
                CAST(SUM(p1_diff) AS INT) as p1,
                CAST(SUM(p2_diff) AS INT) as p2,
                CAST(SUM(p3_diff) AS INT) as p3,
                CAST(SUM(p4_diff) AS INT) as p4,
                CAST(SUM(p5_diff) AS INT) as p5,
                CAST(SUM(p6_diff) AS INT) as p6,
                CAST((SUM(p1_diff) + SUM(p2_diff) + SUM(p3_diff) + SUM(p4_diff) + SUM(p5_diff) + SUM(p6_diff)) AS INT) as total_diff
            FROM team_tactical_stats
            GROUP BY team
            ORDER BY total_diff DESC
        """).fetchdf()

        # 4. Reception Targets (Alvos de Saque)
        targets_df = conn.execute("""
            SELECT 
                p.player_name,
                p.team,
                p.is_libero,
                COUNT(DISTINCT p.match_id) as matches,
                CAST(SUM(p.reception_attempts) AS INT) as rec_attempts,
                CAST(SUM(p.reception_errors) AS INT) as rec_errors,
                ROUND(SUM(p.reception_errors) * 100.0 / NULLIF(SUM(p.reception_attempts), 0), 1) as err_pct,
                ROUND(AVG(p.reception_positive_pct), 1) as avg_pos_pct,
                ROUND(AVG(p.reception_excellent_pct), 1) as avg_exc_pct
            FROM player_match_stats p
            GROUP BY p.player_name, p.team, p.is_libero
            HAVING SUM(p.reception_attempts) >= 30
            ORDER BY rec_attempts DESC
            LIMIT 15
        """).fetchdf()

        # 5. Usage Leaders (Concentração de Carga de Ataque)
        usage_df = conn.execute("""
            WITH team_totals AS (
                SELECT team, SUM(attack_attempts) as team_att_total
                FROM player_match_stats
                GROUP BY team
            )
            SELECT 
                p.player_name,
                p.team,
                COUNT(DISTINCT p.match_id) as matches,
                CAST(SUM(p.points_total) AS INT) as pts,
                CAST(SUM(p.attack_attempts) AS INT) as att,
                ROUND(SUM(p.attack_attempts) * 100.0 / tt.team_att_total, 1) as usage_pct,
                CAST(SUM(p.attack_points) AS INT) as atk_pts,
                ROUND(SUM(p.attack_points) * 100.0 / NULLIF(SUM(p.attack_attempts), 0), 1) as kill_pct,
                ROUND((SUM(p.attack_points) - SUM(p.attack_errors) - SUM(p.attack_blocked)) * 100.0 / NULLIF(SUM(p.attack_attempts), 0), 1) as eff_pct
            FROM player_match_stats p
            JOIN team_totals tt ON p.team = tt.team
            GROUP BY p.player_name, p.team, tt.team_att_total
            HAVING SUM(p.attack_attempts) >= 40
            ORDER BY usage_pct DESC
            LIMIT 15
        """).fetchdf()

    return {
        "sideout_breakpoint": so_bp_df,
        "phase_attacks": phase_df,
        "rotations": rot_df,
        "reception_targets": targets_df,
        "offensive_usage": usage_df,
    }


def display_competition_tactics() -> None:
    """Renders formatted competition-wide tactical intelligence to terminal."""
    data = get_competition_tactical_summary()

    console.print(Panel("[bold yellow]INTELIGÊNCIA TÁTICA DA COMPETIÇÃO — CBS SUB-18[/bold yellow]\n[dim]Consolidação completa de todas as partidas da competição[/dim]", expand=False))

    # 1. SIDE-OUT & BREAK POINT
    console.print("\n[bold cyan]1. RANKING DE SIDE-OUT (SO) & BREAK POINT (BP)[/bold cyan]")
    t1 = Table(show_header=True, header_style="bold magenta")
    t1.add_column("Equipe")
    t1.add_column("Jogos", justify="center")
    t1.add_column("SO Pts / Rec", justify="center")
    t1.add_column("SO %", justify="center")
    t1.add_column("SO Taxa", justify="center")
    t1.add_column("BP Pts / Saques", justify="center")
    t1.add_column("BP %", justify="center")
    t1.add_column("BP Taxa", justify="center")

    for _, r in data["sideout_breakpoint"].iterrows():
        so_pct_style = "bold green" if r["so_pct"] >= 53.0 else ("yellow" if r["so_pct"] >= 48.0 else "red")
        bp_pct_style = "bold green" if r["bp_pct"] >= 26.0 else ("yellow" if r["bp_pct"] >= 22.0 else "red")
        t1.add_row(
            r["team"],
            str(r["matches"]),
            f"{r['so_points']} / {r['so_receptions']}",
            f"[{so_pct_style}]{r['so_pct']}%[/{so_pct_style}]",
            f"{r['so_rate']:.2f} rec = 1 pt",
            f"{r['bp_points']} / {r['bp_serves']}",
            f"[{bp_pct_style}]{r['bp_pct']}%[/{bp_pct_style}]",
            f"{r['bp_rate']:.2f} sq = 1 BP",
        )
    console.print(t1)

    # 2. PHASE ATTACK (K1+, K1-, K2)
    console.print("\n[bold cyan]2. EFICIÊNCIA DE ATAQUE POR FASE: K1+ (Passe #+), K1- (Passe !-) e K2 (Transição)[/bold cyan]")
    t2 = Table(show_header=True, header_style="bold magenta")
    t2.add_column("Equipe")
    t2.add_column("K1+ (Vol | Kill% | Efic%)", justify="center")
    t2.add_column("K1- (Vol | Kill% | Efic%)", justify="center")
    t2.add_column("K2 Transição (Vol | Kill% | Efic%)", justify="center")

    for _, r in data["phase_attacks"].iterrows():
        t2.add_row(
            r["team"],
            f"{r['k1_pos_att']} att | {r['k1_pos_kill_pct']}% | [bold green]{r['k1_pos_eff_pct']}%[/bold green]",
            f"{r['k1_neg_att']} att | {r['k1_neg_kill_pct']}% | [bold yellow]{r['k1_neg_eff_pct']}%[/bold yellow]",
            f"{r['k2_att']} att | {r['k2_kill_pct']}% | [bold cyan]{r['k2_eff_pct']}%[/bold cyan]",
        )
    console.print(t2)

    # 3. ROTATIONS MATRIX (P1..P6)
    console.print("\n[bold cyan]3. MATRIZ DE ROTAÇÕES DO LEVANTADOR (SALDO DE PONTOS P1 A P6)[/bold cyan]")
    t3 = Table(show_header=True, header_style="bold magenta")
    t3.add_column("Equipe")
    t3.add_column("P1", justify="center")
    t3.add_column("P2", justify="center")
    t3.add_column("P3", justify="center")
    t3.add_column("P4", justify="center")
    t3.add_column("P5", justify="center")
    t3.add_column("P6", justify="center")
    t3.add_column("Saldo Geral", justify="center")

    for _, r in data["rotations"].iterrows():
        cells = []
        for p in ["p1", "p2", "p3", "p4", "p5", "p6"]:
            val = r[p]
            val_str = f"+{val}" if val > 0 else str(val)
            color = "green" if val > 0 else ("red" if val < 0 else "dim")
            cells.append(f"[{color}]{val_str}[/{color}]")
        tot = r["total_diff"]
        tot_str = f"+{tot}" if tot > 0 else str(tot)
        tot_color = "bold green" if tot > 0 else ("bold red" if tot < 0 else "dim")
        t3.add_row(r["team"], *cells, f"[{tot_color}]{tot_str}[/{tot_color}]")
    console.print(t3)

    # 4. RECEPTION TARGETS
    console.print("\n[bold cyan]4. ALVOS DE SAQUE (ATLETAS MAIS TESTADOS NA RECEPÇÃO)[/bold cyan]")
    t4 = Table(show_header=True, header_style="bold magenta")
    t4.add_column("Atleta")
    t4.add_column("Equipe")
    t4.add_column("Pos", justify="center")
    t4.add_column("Jogos", justify="center")
    t4.add_column("Recepções", justify="center")
    t4.add_column("Erros", justify="center")
    t4.add_column("Erro %", justify="center")
    t4.add_column("Positiva %", justify="center")
    t4.add_column("Excelente %", justify="center")

    for _, r in data["reception_targets"].iterrows():
        pos = "Líbero" if r["is_libero"] else "Ponteiro"
        err_style = "bold red" if r["err_pct"] >= 8.0 else ("green" if r["err_pct"] <= 4.0 else "yellow")
        t4.add_row(
            r["player_name"],
            r["team"],
            pos,
            str(r["matches"]),
            str(r["rec_attempts"]),
            str(r["rec_errors"]),
            f"[{err_style}]{r['err_pct']}%[/{err_style}]",
            f"{r['avg_pos_pct']}%",
            f"{r['avg_exc_pct']}%",
        )
    console.print(t4)

    # 5. USAGE LEADERS
    console.print("\n[bold cyan]5. SOBRECARGA OFENSIVA (USAGE RATE — CONCENTRAÇÃO DE ATAQUE)[/bold cyan]")
    t5 = Table(show_header=True, header_style="bold magenta")
    t5.add_column("Atleta")
    t5.add_column("Equipe")
    t5.add_column("Jogos", justify="center")
    t5.add_column("Pts Tot", justify="center")
    t5.add_column("Ataques", justify="center")
    t5.add_column("Usage %", justify="center")
    t5.add_column("Kill %", justify="center")
    t5.add_column("Eficiência %", justify="center")

    for _, r in data["offensive_usage"].iterrows():
        usage_style = "bold red" if r["usage_pct"] >= 35.0 else ("bold yellow" if r["usage_pct"] >= 28.0 else "cyan")
        t5.add_row(
            r["player_name"],
            r["team"],
            str(r["matches"]),
            str(r["pts"]),
            str(r["att"]),
            f"[{usage_style}]{r['usage_pct']}%[/{usage_style}]",
            f"{r['kill_pct']}%",
            f"{r['eff_pct']}%",
        )
    console.print(t5)
    console.print()


def get_team_tactical_dossier(team_query: str) -> Optional[Dict[str, Any]]:
    """Fetches in-depth tactical scouting intelligence for a specific team."""
    with default_repo.get_connection() as conn:
        # Match team name
        teams = conn.execute(
            "SELECT DISTINCT team FROM team_tactical_stats WHERE UPPER(team) LIKE UPPER(?)",
            [f"%{team_query.strip()}%"],
        ).fetchall()

        if not teams:
            return None
        team_name = teams[0][0]

        # 1. Record & Sets
        matches = conn.execute("""
            SELECT 
                COUNT(*) as games,
                SUM(CASE WHEN (home_team = ? AND home_sets > away_sets) OR (away_team = ? AND away_sets > home_sets) THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN (home_team = ? AND home_sets < away_sets) OR (away_team = ? AND away_sets < home_sets) THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN home_team = ? THEN home_sets ELSE away_sets END) as sets_won,
                SUM(CASE WHEN home_team = ? THEN away_sets ELSE home_sets END) as sets_lost
            FROM matches
            WHERE home_team = ? OR away_team = ?
        """, [team_name, team_name, team_name, team_name, team_name, team_name, team_name, team_name]).fetchone()

        # 2. Tactical Averages
        tac_df = conn.execute("""
            SELECT 
                CAST(SUM(sideout_points) AS INT) as so_pts,
                CAST(SUM(sideout_receptions) AS INT) as rec_tot,
                ROUND(SUM(sideout_points) * 100.0 / NULLIF(SUM(sideout_receptions), 0), 1) as so_pct,
                ROUND(SUM(sideout_receptions) * 1.0 / NULLIF(SUM(sideout_points), 0), 2) as so_rate,
                CAST(SUM(breakpoint_points) AS INT) as bp_pts,
                CAST(SUM(breakpoint_serves) AS INT) as srv_tot,
                ROUND(SUM(breakpoint_points) * 100.0 / NULLIF(SUM(breakpoint_serves), 0), 1) as bp_pct,
                ROUND(SUM(breakpoint_serves) * 1.0 / NULLIF(SUM(breakpoint_points), 0), 2) as bp_rate,
                CAST(SUM(p1_diff) AS INT) as p1, CAST(SUM(p2_diff) AS INT) as p2, CAST(SUM(p3_diff) AS INT) as p3,
                CAST(SUM(p4_diff) AS INT) as p4, CAST(SUM(p5_diff) AS INT) as p5, CAST(SUM(p6_diff) AS INT) as p6,
                CAST(SUM(pos_rec_att_attempts) AS INT) as k1_pos_att, CAST(SUM(pos_rec_att_points) AS INT) as k1_pos_pts,
                CAST(SUM(pos_rec_att_errors) AS INT) as k1_pos_err, CAST(SUM(pos_rec_att_blocked) AS INT) as k1_pos_blo,
                CAST(SUM(neg_rec_att_attempts) AS INT) as k1_neg_att, CAST(SUM(neg_rec_att_points) AS INT) as k1_neg_pts,
                CAST(SUM(neg_rec_att_errors) AS INT) as k1_neg_err, CAST(SUM(neg_rec_att_blocked) AS INT) as k1_neg_blo,
                CAST(SUM(trans_att_attempts) AS INT) as k2_att, CAST(SUM(trans_att_points) AS INT) as k2_pts,
                CAST(SUM(trans_att_errors) AS INT) as k2_err, CAST(SUM(trans_att_blocked) AS INT) as k2_blo
            FROM team_tactical_stats
            WHERE team = ?
        """, [team_name]).fetchdf()
        t_dict = tac_df.to_dict(orient="records")[0]

        # 3. Top Attackers
        team_att_tot = (t_dict["k1_pos_att"] or 0) + (t_dict["k1_neg_att"] or 0) + (t_dict["k2_att"] or 0)
        attackers = conn.execute("""
            SELECT 
                player_name,
                CAST(SUM(COALESCE(points_total, 0)) AS INT) as pts,
                CAST(SUM(COALESCE(attack_attempts, 0)) AS INT) as att,
                CAST(SUM(COALESCE(attack_points, 0)) AS INT) as atk_pts,
                ROUND(SUM(COALESCE(attack_points, 0)) * 100.0 / NULLIF(SUM(attack_attempts), 0), 1) as kill_pct,
                ROUND((SUM(COALESCE(attack_points, 0)) - SUM(COALESCE(attack_errors, 0)) - SUM(COALESCE(attack_blocked, 0))) * 100.0 / NULLIF(SUM(attack_attempts), 0), 1) as eff_pct
            FROM player_match_stats
            WHERE team = ?
            GROUP BY player_name
            HAVING SUM(attack_attempts) > 0
            ORDER BY att DESC
            LIMIT 6
        """, [team_name]).fetchdf()
        attackers["usage_pct"] = (attackers["att"] * 100.0 / team_att_tot).round(1) if team_att_tot > 0 else 0.0

        # 4. Receivers Line
        receivers = conn.execute("""
            SELECT 
                player_name,
                is_libero,
                CAST(SUM(COALESCE(reception_attempts, 0)) AS INT) as rec,
                CAST(SUM(COALESCE(reception_errors, 0)) AS INT) as err,
                ROUND(SUM(COALESCE(reception_errors, 0)) * 100.0 / NULLIF(SUM(reception_attempts), 0), 1) as err_pct,
                ROUND(AVG(reception_positive_pct), 1) as pos_pct,
                ROUND(AVG(reception_excellent_pct), 1) as exc_pct
            FROM player_match_stats
            WHERE team = ?
            GROUP BY player_name, is_libero
            HAVING SUM(reception_attempts) > 0
            ORDER BY rec DESC
            LIMIT 5
        """, [team_name]).fetchdf()

        # 5. Set breakdown
        sets_dist = conn.execute("""
            SELECT 
                CAST(set_number AS INT) as set_number,
                COUNT(*) as sets_played,
                CAST(SUM(COALESCE(serve_points_won, 0)) AS INT) as ser_pts,
                CAST(SUM(COALESCE(attack_points_won, 0)) AS INT) as atk_pts,
                CAST(SUM(COALESCE(block_points_won, 0)) AS INT) as blo_pts,
                CAST(SUM(COALESCE(opponent_errors_won, 0)) AS INT) as operr_pts
            FROM set_tactical_stats
            WHERE team = ?
            GROUP BY set_number
            ORDER BY set_number
        """, [team_name]).fetchdf()

    return {
        "team": team_name,
        "record": {
            "games": matches[0],
            "wins": matches[1],
            "losses": matches[2],
            "sets_won": matches[3],
            "sets_lost": matches[4],
        },
        "totals": t_dict,
        "attackers": attackers,
        "receivers": receivers,
        "sets_dist": sets_dist,
    }


def display_team_tactics(team_query: str) -> None:
    """Renders formatted tactical scouting dossier for a team."""
    dossier = get_team_tactical_dossier(team_query)
    if not dossier:
        console.print(f"[red]Equipe '{team_query}' não encontrada no banco de dados.[/red]")
        return

    team = dossier["team"]
    rec = dossier["record"]
    t = dossier["totals"]

    title = f"DOSSIÊ TÁTICO & SCOUTING: {team}"
    subtitle = f"Campanha: {rec['wins']}V - {rec['losses']}D ({rec['sets_won']} Sets Ganhos, {rec['sets_lost']} Sets Perdidos em {rec['games']} jogos)"
    console.print(Panel(f"[bold yellow]{title}[/bold yellow]\n[cyan]{subtitle}[/cyan]", expand=False))

    # 1. SO & BP
    console.print("\n[bold cyan]1. EFICIÊNCIA DE FASES (SIDE-OUT & BREAK POINT)[/bold cyan]")
    t1 = Table(show_header=True, header_style="bold magenta")
    t1.add_column("Fase")
    t1.add_column("Pontos", justify="center")
    t1.add_column("Volume", justify="center")
    t1.add_column("Taxa de Conversão", justify="center")
    t1.add_column("Índice de Rendimento", justify="center")

    t1.add_row(
        "Side-Out (K1 / Recepção)",
        f"{t['so_pts']} pts",
        f"{t['rec_tot']} recepções",
        f"[bold green]{t['so_pct']}%[/bold green]",
        f"{t['so_rate']:.2f} rec = 1 pt",
    )
    t1.add_row(
        "Break Point (K2 / Saque)",
        f"{t['bp_pts']} pts",
        f"{t['srv_tot']} saques",
        f"[bold cyan]{t['bp_pct']}%[/bold cyan]",
        f"{t['bp_rate']:.2f} sq = 1 BP",
    )
    console.print(t1)

    # 2. Phase Attacks
    console.print("\n[bold cyan]2. EFICIÊNCIA OFENSIVA POR SITUAÇÃO DE PASSE & TRANSIÇÃO[/bold cyan]")
    t2 = Table(show_header=True, header_style="bold magenta")
    t2.add_column("Situação")
    t2.add_column("Tentativas", justify="center")
    t2.add_column("Pontos (Kill %)", justify="center")
    t2.add_column("Bloqueios", justify="center")
    t2.add_column("Erros", justify="center")
    t2.add_column("Eficiência %", justify="center")

    # K1+
    k1_pos_att = t["k1_pos_att"] or 0
    k1_pos_pts = t["k1_pos_pts"] or 0
    k1_pos_err = t["k1_pos_err"] or 0
    k1_pos_blo = t["k1_pos_blo"] or 0
    k1_pos_kill = (k1_pos_pts * 100.0 / k1_pos_att) if k1_pos_att else 0.0
    k1_pos_eff = ((k1_pos_pts - k1_pos_err - k1_pos_blo) * 100.0 / k1_pos_att) if k1_pos_att else 0.0
    t2.add_row("1º Ataque c/ Passe + (#+)", str(k1_pos_att), f"{k1_pos_pts} ({k1_pos_kill:.1f}%)", str(k1_pos_blo), str(k1_pos_err), f"[bold green]{k1_pos_eff:.1f}%[/bold green]")

    # K1-
    k1_neg_att = t["k1_neg_att"] or 0
    k1_neg_pts = t["k1_neg_pts"] or 0
    k1_neg_err = t["k1_neg_err"] or 0
    k1_neg_blo = t["k1_neg_blo"] or 0
    k1_neg_kill = (k1_neg_pts * 100.0 / k1_neg_att) if k1_neg_att else 0.0
    k1_neg_eff = ((k1_neg_pts - k1_neg_err - k1_neg_blo) * 100.0 / k1_neg_att) if k1_neg_att else 0.0
    t2.add_row("1º Ataque c/ Passe - (!-)", str(k1_neg_att), f"{k1_neg_pts} ({k1_neg_kill:.1f}%)", str(k1_neg_blo), str(k1_neg_err), f"[bold yellow]{k1_neg_eff:.1f}%[/bold yellow]")

    # K2
    k2_att = t["k2_att"] or 0
    k2_pts = t["k2_pts"] or 0
    k2_err = t["k2_err"] or 0
    k2_blo = t["k2_blo"] or 0
    k2_kill = (k2_pts * 100.0 / k2_att) if k2_att else 0.0
    k2_eff = ((k2_pts - k2_err - k2_blo) * 100.0 / k2_att) if k2_att else 0.0
    t2.add_row("Transição / Contra-Ataque", str(k2_att), f"{k2_pts} ({k2_kill:.1f}%)", str(k2_blo), str(k2_err), f"[bold cyan]{k2_eff:.1f}%[/bold cyan]")
    console.print(t2)

    # 3. Rotations P1..P6
    console.print("\n[bold cyan]3. MAPA DE ROTAÇÕES DO LEVANTADOR (P1 A P6)[/bold cyan]")
    t3 = Table(show_header=True, header_style="bold magenta")
    for p in range(1, 7):
        t3.add_column(f"P{p}", justify="center")
    t3.add_column("Saldo Acumulado", justify="center")

    rot_cells = []
    tot_rot = sum((t[f"p{p}"] or 0) for p in range(1, 7))
    for p in range(1, 7):
        val = t[f"p{p}"] or 0
        v_str = f"+{val}" if val > 0 else str(val)
        col = "green" if val > 0 else ("red" if val < 0 else "dim")
        rot_cells.append(f"[{col}]{v_str}[/{col}]")
    tot_col = "bold green" if tot_rot > 0 else ("bold red" if tot_rot < 0 else "dim")
    t3.add_row(*rot_cells, f"[{tot_col}]{'+' if tot_rot > 0 else ''}{tot_rot}[/{tot_col}]")
    console.print(t3)

    # Destaques
    rots = {f"P{p}": (t[f"p{p}"] or 0) for p in range(1, 7)}
    best_rot = max(rots.items(), key=lambda x: x[1])
    worst_rot = min(rots.items(), key=lambda x: x[1])
    console.print(f"[dim]• Ponto forte do rodízio: [bold green]{best_rot[0]} ({'+' if best_rot[1]>0 else ''}{best_rot[1]} pts)[/bold green] | Ponto fraco / alvo tático: [bold red]{worst_rot[0]} ({'+' if worst_rot[1]>0 else ''}{worst_rot[1]} pts)[/bold red][/dim]")

    # 4. Top Attackers (Offensive Distribution)
    console.print("\n[bold cyan]4. DISTRIBUIÇÃO OFENSIVA & PRINCIPAIS ATACANTES[/bold cyan]")
    t4 = Table(show_header=True, header_style="bold magenta")
    t4.add_column("Atleta")
    t4.add_column("Pontos Tot", justify="center")
    t4.add_column("Ataques", justify="center")
    t4.add_column("Usage %", justify="center")
    t4.add_column("Kill %", justify="center")
    t4.add_column("Eficiência %", justify="center")

    for _, r in dossier["attackers"].iterrows():
        kill_str = "0.0%" if pd.isna(r["kill_pct"]) else f"{r['kill_pct']:.1f}%"
        eff_str = "0.0%" if pd.isna(r["eff_pct"]) else f"{r['eff_pct']:.1f}%"
        t4.add_row(
            r["player_name"],
            str(r["pts"]),
            str(r["att"]),
            f"[bold cyan]{r['usage_pct']}%[/bold cyan]",
            kill_str,
            eff_str,
        )
    console.print(t4)

    # 5. Receivers
    console.print("\n[bold cyan]5. LINHA DE PASSE (ESTABILIDADE DA RECEPÇÃO)[/bold cyan]")
    t5 = Table(show_header=True, header_style="bold magenta")
    t5.add_column("Atleta")
    t5.add_column("Posição", justify="center")
    t5.add_column("Volume Rec", justify="center")
    t5.add_column("Erros", justify="center")
    t5.add_column("Erro %", justify="center")
    t5.add_column("Positiva %", justify="center")
    t5.add_column("Excelente %", justify="center")

    for _, r in dossier["receivers"].iterrows():
        err_pct_str = "0.0%" if pd.isna(r["err_pct"]) else f"{r['err_pct']:.1f}%"
        pos_pct_str = "0.0%" if pd.isna(r["pos_pct"]) else f"{r['pos_pct']:.1f}%"
        exc_pct_str = "0.0%" if pd.isna(r["exc_pct"]) else f"{r['exc_pct']:.1f}%"
        t5.add_row(
            r["player_name"],
            "Líbero" if r["is_libero"] else "Ponteiro",
            str(r["rec"]),
            str(r["err"]),
            err_pct_str,
            pos_pct_str,
            exc_pct_str,
        )
    console.print(t5)

    # 6. Sets Distribution
    console.print("\n[bold cyan]6. DE ONDE VÊM OS PONTOS DA EQUIPE POR SET (ORIGEM)[/bold cyan]")
    t6 = Table(show_header=True, header_style="bold magenta")
    t6.add_column("Set", justify="center")
    t6.add_column("Sets Disputados", justify="center")
    t6.add_column("Saque (Aces)", justify="center")
    t6.add_column("Ataque", justify="center")
    t6.add_column("Bloqueio", justify="center")
    t6.add_column("Erros Adversários", justify="center")

    for _, r in dossier["sets_dist"].iterrows():
        t6.add_row(
            f"Set {r['set_number']}",
            str(r["sets_played"]),
            f"{r['ser_pts']} pts",
            f"{r['atk_pts']} pts",
            f"{r['blo_pts']} pts",
            f"[bold yellow]{r['operr_pts']} pts[/bold yellow]",
        )
    console.print(t6)
    console.print()


def display_head_to_head_tactics(team_a_query: str, team_b_query: str) -> None:
    """Renders head-to-head tactical comparison and matchup scouting report."""
    dossier_a = get_team_tactical_dossier(team_a_query)
    dossier_b = get_team_tactical_dossier(team_b_query)

    if not dossier_a:
        console.print(f"[red]Equipe '{team_a_query}' não encontrada no banco.[/red]")
        return
    if not dossier_b:
        console.print(f"[red]Equipe '{team_b_query}' não encontrada no banco.[/red]")
        return

    ta = dossier_a["team"]
    tb = dossier_b["team"]
    da = dossier_a["totals"]
    db = dossier_b["totals"]

    title = f"CONFRONTO TÁTICO & SCOUTING: {ta} × {tb}"
    console.print(Panel(f"[bold yellow]{title}[/bold yellow]\n[dim]Análise comparativa direta baseada no histórico de toda a competição[/dim]", expand=False))

    # 1. SO & BP
    console.print("\n[bold cyan]1. DISPUTA DE FASES (SIDE-OUT & BREAK POINT)[/bold cyan]")
    t1 = Table(show_header=True, header_style="bold magenta")
    t1.add_column("Métrica de Fase")
    t1.add_column(ta, justify="center")
    t1.add_column(tb, justify="center")
    t1.add_column("Vantagem Tática", justify="center")

    so_adv = ta if da["so_pct"] > db["so_pct"] else (tb if db["so_pct"] > da["so_pct"] else "Empate")
    bp_adv = ta if da["bp_pct"] > db["bp_pct"] else (tb if db["bp_pct"] > da["bp_pct"] else "Empate")

    t1.add_row(
        "Side-Out % (Conversão de Passe)",
        f"{da['so_pct']}% ({da['so_rate']:.2f} rec/pt)",
        f"{db['so_pct']}% ({db['so_rate']:.2f} rec/pt)",
        f"[bold green]{so_adv}[/bold green]",
    )
    t1.add_row(
        "Break Point % (Conversão de Saque)",
        f"{da['bp_pct']}% ({da['bp_rate']:.2f} sq/BP)",
        f"{db['bp_pct']}% ({db['bp_rate']:.2f} sq/BP)",
        f"[bold green]{bp_adv}[/bold green]",
    )
    console.print(t1)

    # 2. Phase Attacks
    console.print("\n[bold cyan]2. EFICIÊNCIA OFENSIVA POR SITUAÇÃO (PASSE #+, PASSE !- E TRANSIÇÃO)[/bold cyan]")
    t2 = Table(show_header=True, header_style="bold magenta")
    t2.add_column("Fase Ofensiva")
    t2.add_column(f"{ta} (Kill% | Efic%)", justify="center")
    t2.add_column(f"{tb} (Kill% | Efic%)", justify="center")
    t2.add_column("Vantagem Ofensiva", justify="center")

    # K1+
    a_k1_kill = (da["k1_pos_pts"] * 100.0 / da["k1_pos_att"]) if da["k1_pos_att"] else 0.0
    a_k1_eff = ((da["k1_pos_pts"] - da["k1_pos_err"] - da["k1_pos_blo"]) * 100.0 / da["k1_pos_att"]) if da["k1_pos_att"] else 0.0
    b_k1_kill = (db["k1_pos_pts"] * 100.0 / db["k1_pos_att"]) if db["k1_pos_att"] else 0.0
    b_k1_eff = ((db["k1_pos_pts"] - db["k1_pos_err"] - db["k1_pos_blo"]) * 100.0 / db["k1_pos_att"]) if db["k1_pos_att"] else 0.0
    k1_adv = ta if a_k1_eff > b_k1_eff else (tb if b_k1_eff > a_k1_eff else "Empate")
    t2.add_row(
        "1º Ataque c/ Passe + (#+)",
        f"{a_k1_kill:.1f}% | {a_k1_eff:.1f}%",
        f"{b_k1_kill:.1f}% | {b_k1_eff:.1f}%",
        f"[bold green]{k1_adv}[/bold green]",
    )

    # K1-
    a_neg_kill = (da["k1_neg_pts"] * 100.0 / da["k1_neg_att"]) if da["k1_neg_att"] else 0.0
    a_neg_eff = ((da["k1_neg_pts"] - da["k1_neg_err"] - da["k1_neg_blo"]) * 100.0 / da["k1_neg_att"]) if da["k1_neg_att"] else 0.0
    b_neg_kill = (db["k1_neg_pts"] * 100.0 / db["k1_neg_att"]) if db["k1_neg_att"] else 0.0
    b_neg_eff = ((db["k1_neg_pts"] - db["k1_neg_err"] - db["k1_neg_blo"]) * 100.0 / db["k1_neg_att"]) if db["k1_neg_att"] else 0.0
    neg_adv = ta if a_neg_eff > b_neg_eff else (tb if b_neg_eff > a_neg_eff else "Empate")
    t2.add_row(
        "1º Ataque c/ Passe - (!-)",
        f"{a_neg_kill:.1f}% | {a_neg_eff:.1f}%",
        f"{b_neg_kill:.1f}% | {b_neg_eff:.1f}%",
        f"[bold yellow]{neg_adv}[/bold yellow]",
    )

    # K2
    a_k2_kill = (da["k2_pts"] * 100.0 / da["k2_att"]) if da["k2_att"] else 0.0
    a_k2_eff = ((da["k2_pts"] - da["k2_err"] - da["k2_blo"]) * 100.0 / da["k2_att"]) if da["k2_att"] else 0.0
    b_k2_kill = (db["k2_pts"] * 100.0 / db["k2_att"]) if db["k2_att"] else 0.0
    b_k2_eff = ((db["k2_pts"] - db["k2_err"] - db["k2_blo"]) * 100.0 / db["k2_att"]) if db["k2_att"] else 0.0
    k2_adv = ta if a_k2_eff > b_k2_eff else (tb if b_k2_eff > a_k2_eff else "Empate")
    t2.add_row(
        "Transição / Contra-Ataque",
        f"{a_k2_kill:.1f}% | {a_k2_eff:.1f}%",
        f"{b_k2_kill:.1f}% | {b_k2_eff:.1f}%",
        f"[bold cyan]{k2_adv}[/bold cyan]",
    )
    console.print(t2)

    # 3. Rotations Matchup
    console.print("\n[bold cyan]3. CONFRONTO DE ROTAÇÕES (SALDO P1 A P6)[/bold cyan]")
    t3 = Table(show_header=True, header_style="bold magenta")
    t3.add_column("Rotação")
    t3.add_column(f"{ta} (Saldo)", justify="center")
    t3.add_column(f"{tb} (Saldo)", justify="center")
    t3.add_column("Diagnóstico Tático", justify="center")

    for p in range(1, 7):
        va = da[f"p{p}"] or 0
        vb = db[f"p{p}"] or 0
        va_str = f"+{va}" if va > 0 else str(va)
        vb_str = f"+{vb}" if vb > 0 else str(vb)
        ca = "green" if va > 0 else ("red" if va < 0 else "dim")
        cb = "green" if vb > 0 else ("red" if vb < 0 else "dim")

        if va > 0 and vb < 0:
            diag = f"[bold green]Janela de quebra para {ta} (atacar aqui)[/bold green]"
        elif vb > 0 and va < 0:
            diag = f"[bold red]Zona de perigo para {ta} (pressão de {tb})[/bold red]"
        else:
            diag = "Equilibrado"

        t3.add_row(f"P{p}", f"[{ca}]{va_str}[/{ca}]", f"[{cb}]{vb_str}[/{cb}]", diag)
    console.print(t3)

    # 4. Scouting Targets
    console.print("\n[bold cyan]4. ALVOS RECOMENDADOS PARA A ESTRATÉGIA DE SAQUE[/bold cyan]")
    # Target in Team B for Team A
    tb_rec = dossier_b["receivers"]
    if not tb_rec.empty:
        tb_target = tb_rec.sort_values(by="err_pct", ascending=False).iloc[0]
        console.print(f"• [bold yellow]Para {ta} sacar contra {tb}:[/bold yellow] Pressionar [bold red]{tb_target['player_name']}[/bold red] ({tb_target['err_pct']:.1f}% erros, {tb_target['pos_pct']:.1f}% positivo em {tb_target['rec']} recepções).")

    # Target in Team A for Team B
    ta_rec = dossier_a["receivers"]
    if not ta_rec.empty:
        ta_target = ta_rec.sort_values(by="err_pct", ascending=False).iloc[0]
        console.print(f"• [bold yellow]Para {tb} sacar contra {ta}:[/bold yellow] Pressionar [bold red]{ta_target['player_name']}[/bold red] ({ta_target['err_pct']:.1f}% erros, {ta_target['pos_pct']:.1f}% positivo em {ta_target['rec']} recepções).")
    console.print()

