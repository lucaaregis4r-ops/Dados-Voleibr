"""Command-line interface for CBV Volley Data."""

from typing import Optional
import typer
from rich.console import Console

app = typer.Typer(
    name="cbv",
    help="CBV Volley Data — Coleta, processamento e análise de dados de voleibol da CBV.",
    add_completion=False,
)
console = Console()


@app.callback()
def main():
    """CBV Volley Data CLI."""
    pass


@app.command("scrape-game")
def scrape_game_cmd(
    game_id: int = typer.Argument(..., help="ID numérico da partida na CBV (ex: 2590834)"),
    force: bool = typer.Option(False, "--force", "-f", help="Força novo download mesmo se já existir em cache"),
):
    """Raspa e baixa relatório da partida."""
    from cbv.scraper.downloader import process_single_game

    process_single_game(game_id, force=force)


@app.command("scrape-competition")
def scrape_competition_cmd(
    competition: str = typer.Option("cbs", "--competition", help="Código da competição (ex: cbs)"),
    category: str = typer.Option("sub18", "--category", help="Categoria (ex: sub18)"),
    gender: str = typer.Option("masculino", "--gender", help="Gênero (masculino/feminino)"),
    division: str = typer.Option("especial", "--division", help="Divisão (ex: especial)"),
    season: int = typer.Option(2026, "--season", help="Ano da temporada"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limite máximo de partidas para processar"),
    force: bool = typer.Option(False, "--force", "-f", help="Força reprocessamento"),
):
    """Raspa todos os jogos de uma competição."""
    from cbv.scraper.competition import scrape_competition

    scrape_competition(
        competition=competition,
        category=category,
        gender=gender,
        division=division,
        season=season,
        force=force,
        limit=limit,
    )


@app.command("rankings")
def rankings_cmd(
    competition: str = typer.Option("CBS SUB-18 MASCULINO", "--competition", "-c", help="Título da competição"),
    min_attack: int = typer.Option(10, "--min-attack", help="Mínimo de tentativas de ataque para ranking"),
    min_serve: int = typer.Option(10, "--min-serve", help="Mínimo de saques para ranking"),
):
    """Exibe rankings estatísticos consolidados."""
    from cbv.analysis.rankings import display_rankings

    display_rankings(
        competition_title=competition,
        min_attack_attempts=min_attack,
        min_serve_attempts=min_serve,
    )


@app.command("match-tactics")
def match_tactics_cmd(
    match_id: int = typer.Argument(..., help="ID numérico da partida (ex: 2590834)"),
):
    """Exibe relatório tático detalhado de uma partida (Side-out, Break point, K1/K2, Rotações P1-P6)."""
    from cbv.analysis.tactics import display_match_tactics

    display_match_tactics(match_id)


@app.command("competition-tactics")
def competition_tactics_cmd():
    """Exibe inteligência tática consolidada de toda a competição (SO/BP, K1/K2, Matriz P1-P6, Alvos de Saque, Carga Ofensiva)."""
    from cbv.analysis.tactics import display_competition_tactics

    display_competition_tactics()


@app.command("team-tactics")
def team_tactics_cmd(
    team: str = typer.Argument(..., help="Nome ou sigla da equipe (ex: 'SÃO PAULO', 'PARANÁ', 'MINAS')"),
):
    """Exibe dossiê tático e relatório de scouting completo de uma equipe."""
    from cbv.analysis.tactics import display_team_tactics

    display_team_tactics(team)


@app.command("compare")
def compare_cmd(
    team_a: str = typer.Argument(..., help="Primeira equipe do confronto"),
    team_b: str = typer.Argument(..., help="Segunda equipe do confronto"),
):
    """Gera relatório de confronto tático direto (Head-to-Head Matchup Scouting)."""
    from cbv.analysis.tactics import display_head_to_head_tactics

    display_head_to_head_tactics(team_a, team_b)


@app.command("dashboard")
def dashboard_cmd(
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Abre o dashboard automaticamente no navegador"),
):
    """Compila dados e gera o Dashboard HTML interativo com visão de scouting completa."""
    import webbrowser
    from cbv.export.html_dashboard import export_dashboard_html

    html_path = export_dashboard_html()
    if open_browser:
        console.print(f"[dim]Abrindo no navegador: {html_path.resolve()}[/dim]")
        webbrowser.open(html_path.resolve().as_uri())


export_app = typer.Typer(help="Exporta dados do banco e rankings para arquivos externos.")
app.add_typer(export_app, name="export")


@export_app.command("html")
def export_html_cmd():
    """Exporta o Dashboard HTML interativo e independente."""
    from cbv.export.html_dashboard import export_dashboard_html

    export_dashboard_html()


@export_app.command("csv")
def export_csv_cmd():
    """Exporta todas as tabelas e rankings para arquivos CSV."""
    from cbv.export.csv_export import export_all_to_csv

    export_all_to_csv()


@export_app.command("json")
def export_json_cmd():
    """Exporta dados e rankings consolidados para arquivos JSON."""
    from cbv.export.json_export import export_all_to_json

    export_all_to_json()


@app.command("retry-failed")
def retry_failed_cmd():
    """Tenta novamente partidas registradas no data/failed_games.json."""
    from cbv.scraper.competition import load_failed_games, save_failed_games
    from cbv.scraper.downloader import process_single_game

    failed = load_failed_games()
    if not failed:
        console.print("[green]Nenhuma partida com falha pendente no histórico.[/green]")
        return

    console.print(f"[bold]Reprocessando {len(failed)} partida(s) com falha prévia...[/bold]\n")
    still_failed = []
    for item in failed:
        mid = item["match_id"]
        try:
            process_single_game(mid, force=True)
            console.print(f"[green]✓ Partida {mid} reprocessada com sucesso![/green]\n")
        except Exception as e:
            console.print(f"[red]✗ Partida {mid} continuou falhando: {e}[/red]\n")
            still_failed.append({"match_id": mid, "reason": str(e)})

    save_failed_games(still_failed)
    console.print(f"[dim]Concluído: {len(failed) - len(still_failed)} recuperadas, {len(still_failed)} pendentes.[/dim]")




if __name__ == "__main__":
    app()
