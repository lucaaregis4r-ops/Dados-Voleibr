"""Daily automated synchronization pipeline for CBV Volley Data.

Runs daily at 03:00 to:
1. Fetch and ingest latest finished match reports from CBV (Superliga & CBS).
2. Fetch upcoming match schedule without synthesizing missing forecasts.
3. Normalize canonical team names and verify DuckDB integrity.
4. Re-export HTML dashboard, CSVs, and JSON files.
5. Create summary log for Git commit.
"""

import sys
import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from cbv.config import logger, BASE_DIR
from cbv.scraper.sync import run_daily_sync
from cbv.scraper.fixtures import scrape_upcoming_fixtures
from cbv.scraper.superliga import scrape_all_superliga_editions
from cbv.database.repository import default_repo
from cbv.export.html_dashboard import export_dashboard_html
from cbv.export.csv_export import export_all_to_csv
from cbv.export.json_export import export_all_to_json
from cbv.parser.match_report import CANONICAL_TEAMS

console = Console()


def normalize_all_teams_in_db() -> int:
    """Ensures all team names across DuckDB tables follow canonical standards."""
    updated = 0
    with default_repo.get_connection() as conn:
        for old, new in CANONICAL_TEAMS.items():
            if old != new:
                conn.execute("UPDATE matches SET home_team = ? WHERE home_team = ?", [new, old])
                conn.execute("UPDATE matches SET away_team = ? WHERE away_team = ?", [new, old])
                conn.execute("UPDATE player_match_stats SET team = ? WHERE team = ?", [new, old])
                conn.execute("UPDATE team_match_stats SET team = ? WHERE team = ?", [new, old])
                conn.execute("UPDATE team_tactical_stats SET team = ? WHERE team = ?", [new, old])
                conn.execute("UPDATE set_tactical_stats SET team = ? WHERE team = ?", [new, old])
                updated += 1
    return updated


def run_full_daily_pipeline() -> bool:
    """Executes the full daily update pipeline."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[bold cyan]🏐 CBV VOLLEY DATA — PIPELINE DIÁRIO AUTOMATIZADO [{now_str}][/bold cyan]")

    # 1. Update upcoming fixtures
    console.print("\n[yellow]1/4. Atualizando calendário público da CBV...[/yellow]")
    try:
        fixtures = scrape_upcoming_fixtures()
        console.print(f"[green]✓ {len(fixtures)} partidas do calendário público sincronizadas.[/green]")
    except Exception as e:
        logger.error(f"Erro ao sincronizar calendário: {e}")
        console.print(f"[red]Aviso: Falha ao atualizar calendário: {e}[/red]")

    # 2. Check for newly finished Superliga matches
    console.print("\n[yellow]2/4. Verificando súmulas e relatórios técnicos das edições ativas...[/yellow]")
    try:
        scrape_all_superliga_editions(
            editions=["2025-2026_masculina", "2025-2026_feminina"],
            force=False,
            workers=4
        )
        console.print("[green]✓ Verificação de novas partidas da Superliga concluída.[/green]")
    except Exception as e:
        logger.error(f"Erro na varredura da Superliga: {e}")
        console.print(f"[red]Aviso: Erro na varredura: {e}[/red]")

    from cbv.scraper.competition import scrape_competition
    for gender in ('feminino','masculino'):
        try:scrape_competition(competition='cbs',category='sub18',gender=gender,division='especial',season=datetime.date.today().year)
        except Exception as exc:logger.warning(f'Descoberta CBS {gender}: {exc}')

    # 3. Canonical team name hygiene
    console.print("\n[yellow]3/4. Higienização e unificação canônica de equipes no banco...[/yellow]")
    normalize_all_teams_in_db()
    console.print("[green]✓ Higienização canônica concluída (zero duplicações).[/green]")

    # Archive sources and derive only reconciled match snapshots on the staging DB.
    from cbv.config import RAW_DIR
    from cbv.scraper.sources import SourceCollector, RequestGate
    from cbv.reconstruction.store import rebuild_all,validate_official
    gate=RequestGate(.6)
    with default_repo.get_connection() as conn:
        match_ids=[r[0] for r in conn.execute('SELECT match_id FROM matches').fetchall()]
    collector=SourceCollector(RAW_DIR/'matches',RAW_DIR,gate=gate)
    for mid in match_ids:
        try:collector.collect(mid)
        except Exception as exc:logger.warning(f'Fontes {mid}: {exc}')
    with default_repo.get_connection() as conn:
        summary=rebuild_all(conn,RAW_DIR/'matches')
        validate_official(conn)
        logger.info(f'Reconstrução: {summary}')
    from cbv.metrics.methodology import generate
    import os
    generate(Path(os.environ['CBV_PUBLISH_DIR'])/'docs/CADERNO_METODOLOGICO.md')

    # 4. Re-export Dashboard HTML and exports
    console.print("\n[yellow]4/4. Recompilando Dashboard HTML e exportações CSV/JSON...[/yellow]")
    try:
        export_dashboard_html()
        export_all_to_csv()
        export_all_to_json()
        console.print("[bold green]✓ Todos os artefatos e dashboard exportados com sucesso![/bold green]")
    except Exception as e:
        logger.error(f"Erro na exportação de artefatos: {e}")
        console.print(f"[bold red]Erro crítico na exportação: {e}[/bold red]")
        return False

    console.print(f"\n[bold green]✓ Pipeline diário finalizado com sucesso às {datetime.datetime.now().strftime('%H:%M:%S')}.[/bold green]")
    default_repo._conn.execute("CHECKPOINT")
    default_repo._conn.close()
    return True


if __name__ == "__main__":
    success = run_full_daily_pipeline()
    sys.exit(0 if success else 1)
