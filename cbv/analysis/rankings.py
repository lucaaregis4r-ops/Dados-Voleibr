"""Statistical rankings engine calculating leaders across volleyball fundamentals."""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table

from cbv.database.repository import default_repo
from cbv.analysis.metrics import (
    calc_attack_success_pct,
    calc_attack_efficiency,
    calc_ace_rate,
)

console = Console()


def get_aggregated_player_stats() -> List[Dict[str, Any]]:
    """One player/team aggregate per competition, category, gender and edition."""
    query = """
    SELECT 
        m.competition,m.category,m.gender,m.season,
        player_name,
        team,
        count(distinct match_id) as matches_played,
        sum(coalesce(points_total, 0)) as total_points,
        sum(coalesce(serve_attempts, 0)) as total_serve_attempts,
        sum(coalesce(serve_errors, 0)) as total_serve_errors,
        sum(coalesce(serve_points, 0)) as total_aces,
        sum(coalesce(reception_attempts, 0)) as total_reception_attempts,
        sum(coalesce(reception_errors, 0)) as total_reception_errors,
        sum(coalesce(attack_attempts, 0)) as total_attack_attempts,
        sum(coalesce(attack_errors, 0)) as total_attack_errors,
        sum(coalesce(attack_blocked, 0)) as total_attack_blocked,
        sum(coalesce(attack_points, 0)) as total_attack_points,
        sum(coalesce(block_points, 0)) as total_blocks
    FROM player_match_stats p JOIN matches m USING(match_id)
    WHERE m.validation_status='VALID'
    GROUP BY m.competition,m.category,m.gender,m.season,player_name,team
    """
    with default_repo.get_connection() as conn:
        df = conn.execute(query).fetchdf()

    players = df.to_dict(orient="records")
    for p in players:
        p["attack_success_pct"] = calc_attack_success_pct(
            p["total_attack_points"], p["total_attack_attempts"]
        )
        p["attack_efficiency"] = calc_attack_efficiency(
            p["total_attack_points"],
            p["total_attack_errors"],
            p["total_attack_blocked"],
            p["total_attack_attempts"],
        )
        p["ace_rate"] = calc_ace_rate(p["total_aces"], p["total_serve_attempts"])
    return players


def get_scoring_ranking(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns top scorers by total points."""
    players = get_aggregated_player_stats()
    sorted_players = sorted(players, key=lambda x: x["total_points"], reverse=True)
    return sorted_players[:limit]


def get_attack_ranking(min_attempts: int = 10, limit: int = 5) -> List[Dict[str, Any]]:
    """Returns leaders in attack success percentage with minimum attempt filter."""
    players = [
        p for p in get_aggregated_player_stats()
        if p["total_attack_attempts"] >= min_attempts and p["attack_success_pct"] is not None
    ]
    sorted_players = sorted(players, key=lambda x: x["attack_success_pct"], reverse=True)
    return sorted_players[:limit]


def get_block_ranking(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns top blockers by total block points."""
    players = get_aggregated_player_stats()
    sorted_players = sorted(players, key=lambda x: x["total_blocks"], reverse=True)
    return sorted_players[:limit]


def get_serve_ranking(min_attempts: int = 10, limit: int = 5) -> List[Dict[str, Any]]:
    """Returns top servers by aces and ace rate."""
    players = [
        p for p in get_aggregated_player_stats()
        if p["total_serve_attempts"] >= min_attempts and p["ace_rate"] is not None
    ]
    sorted_players = sorted(players, key=lambda x: (x["total_aces"], x["ace_rate"]), reverse=True)
    return sorted_players[:limit]


def display_rankings(
    competition_title: str = "CBS SUB-18 MASCULINO",
    min_attack_attempts: int = 10,
    min_serve_attempts: int = 10,
) -> None:
    """Renders formatted rankings to terminal output."""
    console.print(f"\n[bold green]{competition_title.upper()}[/bold green]\n")

    # 1. Scoring
    scoring = get_scoring_ranking(limit=5)
    console.print("[bold cyan]PONTUAÇÃO[/bold cyan]")
    if scoring:
        for i, p in enumerate(scoring, start=1):
            console.print(f"{i}. {p['player_name']} — {p['team']} — [bold]{p['total_points']}[/bold] pts")
    else:
        console.print("[dim]Nenhum dado registrado.[/dim]")
    console.print()

    # 2. Attack
    attack = get_attack_ranking(min_attempts=min_attack_attempts, limit=5)
    console.print(f"[bold cyan]ATAQUE[/bold cyan] [dim](mínimo {min_attack_attempts} tentativas)[/dim]")
    if attack:
        for i, p in enumerate(attack, start=1):
            console.print(
                f"{i}. {p['player_name']} — {p['team']} — [bold]{p['attack_success_pct']}%[/bold] "
                f"({p['total_attack_points']}/{p['total_attack_attempts']} att, efic: {p['attack_efficiency']}%)"
            )
    else:
        console.print("[dim]Nenhum atleta atingiu o volume mínimo de ataques.[/dim]")
    console.print()

    # 3. Block
    block = get_block_ranking(limit=5)
    console.print("[bold cyan]BLOQUEIO[/bold cyan]")
    if block:
        for i, p in enumerate(block, start=1):
            console.print(f"{i}. {p['player_name']} — {p['team']} — [bold]{p['total_blocks']}[/bold] blocks")
    else:
        console.print("[dim]Nenhum dado registrado.[/dim]")
    console.print()

    # 4. Serve
    serve = get_serve_ranking(min_attempts=min_serve_attempts, limit=5)
    console.print(f"[bold cyan]SAQUE (ACES)[/bold cyan] [dim](mínimo {min_serve_attempts} saques)[/dim]")
    if serve:
        for i, p in enumerate(serve, start=1):
            console.print(
                f"{i}. {p['player_name']} — {p['team']} — [bold]{p['total_aces']}[/bold] aces "
                f"({p['ace_rate']}% ace rate)"
            )
    else:
        console.print("[dim]Nenhum atleta atingiu o volume mínimo de saques.[/dim]")
    console.print()
