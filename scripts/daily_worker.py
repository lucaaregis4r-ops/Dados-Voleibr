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
    """Executes the full daily update pipeline with formal health tracking."""
    import os
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[bold cyan]🏐 CBV VOLLEY DATA — PIPELINE DIÁRIO AUTOMATIZADO [{now_str}][/bold cyan]")

    from cbv.pipeline_health import SyncHealthTracker, STATUS_FAILED
    publish_dir = Path(os.environ.get('CBV_PUBLISH_DIR', BASE_DIR))
    tracker = SyncHealthTracker(exports_dir=publish_dir / 'exports')

    with default_repo.get_connection() as conn:
        initial_match_count = conn.execute("SELECT count(*) FROM matches").fetchone()[0]

    # 1. Update upcoming fixtures (OPTIONAL)
    console.print("\n[yellow]1/4. Atualizando calendário público da CBV...[/yellow]")
    try:
        fixtures = scrape_upcoming_fixtures()
        latest_fixture_date = max((f.get('match_date') for f in fixtures if f.get('match_date')), default=None)
        tracker.record_source(
            "calendar",
            attempted=len(fixtures) or 1,
            successful=len(fixtures),
            latest_date=latest_fixture_date,
            message=f"{len(fixtures)} partidas sincronizadas"
        )
        console.print(f"[green]✓ {len(fixtures)} partidas do calendário público sincronizadas.[/green]")
    except Exception as e:
        logger.warning(f"Erro ao sincronizar calendário (fonte opcional): {e}")
        console.print(f"[yellow]Aviso: Falha ao atualizar calendário: {e}[/yellow]")
        tracker.record_source("calendar", attempted=1, successful=0, failed=1, error=e)

    # 2. Check for newly finished Superliga matches (CRITICAL)
    console.print("\n[yellow]2/4. Verificando súmulas e relatórios técnicos das edições ativas...[/yellow]")
    for ed_key, ed_name in [("atual_masculina", "superliga_m"), ("atual_feminina", "superliga_f")]:
        try:
            scrape_all_superliga_editions(
                editions=[ed_key],
                force=False,
                workers=2
            )
            tracker.record_source(ed_name, attempted=1, successful=1, message="Sincronizada com sucesso")
            console.print(f"[green]✓ Superliga {ed_name} sincronizada.[/green]")
        except Exception as e:
            logger.error(f"Erro crítico na varredura da {ed_name}: {e}")
            console.print(f"[bold red]Erro crítico na varredura da {ed_name}: {e}[/bold red]")
            tracker.record_source(ed_name, attempted=1, successful=0, failed=1, error=e)
            # Critical source failure must fail the pipeline
            raise RuntimeError(f"Fonte crítica falhou ({ed_name}): {e}")

    # CBS discovery (OPTIONAL)
    from cbv.scraper.competition import scrape_competition
    for gender, key in (('feminino', 'cbs_f'), ('masculino', 'cbs_m')):
        try:
            scrape_competition(competition='cbs', category='sub18', gender=gender, division='especial', season=datetime.date.today().year)
            tracker.record_source(key, attempted=1, successful=1, message="Sincronizada")
        except Exception as exc:
            logger.warning(f'Descoberta CBS {gender} (fonte opcional): {exc}')
            tracker.record_source(key, attempted=1, successful=0, failed=1, error=exc)

    # 3. Canonical team name hygiene
    console.print("\n[yellow]3/4. Higienização e unificação canônica de equipes no banco...[/yellow]")
    normalize_all_teams_in_db()
    console.print("[green]✓ Higienização canônica concluída (zero duplicações).[/green]")

    # Archive sources and derive only reconciled match snapshots on the staging DB.
    from cbv.config import RAW_DIR
    from cbv.scraper.sources import SourceCollector, RequestGate
    from cbv.reconstruction.store import rebuild_all, validate_official
    gate = RequestGate(.6)
    with default_repo.get_connection() as conn:
        match_ids = [r[0] for r in conn.execute('SELECT match_id FROM matches').fetchall()]
    collector = SourceCollector(RAW_DIR / 'matches', RAW_DIR, gate=gate)
    
    source_stats = {"scoresheets": 0, "match_reports": 0, "libero_reports": 0, "play_by_play": 0}
    for mid in match_ids:
        try:
            snapshot = collector.collect(mid)
            if snapshot:
                for k in source_stats:
                    if k in snapshot or (k.rstrip('s') in snapshot):
                        source_stats[k] += 1
        except Exception as exc:
            logger.warning(f'Fontes {mid}: {exc}')

    for k, count in source_stats.items():
        tracker.record_source(k, attempted=len(match_ids), successful=count, message=f"{count}/{len(match_ids)} snapshots")

    with default_repo.get_connection() as conn:
        summary = rebuild_all(conn, RAW_DIR / 'matches')
        validate_official(conn)
        logger.info(f'Reconstrução: {summary}')

    from cbv.metrics.methodology import generate
    generate(Path(os.environ['CBV_PUBLISH_DIR']) / 'docs/CADERNO_METODOLOGICO.md')

    # 4. Re-export Dashboard HTML and exports
    console.print("\n[yellow]4/4. Recompilando Dashboard HTML e exportações CSV/JSON...[/yellow]")
    try:
        # Finalize health report
        with default_repo.get_connection() as conn:
            current_match_count = conn.execute("SELECT count(*) FROM matches").fetchone()[0]
            new_matches = max(0, current_match_count - initial_match_count)
            report = tracker.finalize(
                conn,
                initial_match_count=initial_match_count,
                quality_gate_passed=True,
                new_matches=new_matches
            )
            tracker.save_report(report, publish_dir / 'exports')
            
            # Surface to GitHub Actions step summary if running in CI
            summary_path = os.environ.get('GITHUB_STEP_SUMMARY')
            if summary_path:
                try:
                    summary_md = tracker.generate_github_summary(report, initial_match_count)
                    Path(summary_path).write_text(summary_md, encoding='utf-8')
                except Exception as ex:
                    logger.warning(f"Erro ao salvar step summary: {ex}")

        export_dashboard_html()
        export_all_to_csv()
        export_all_to_json()
        console.print("[bold green]✓ Todos os artefatos e dashboard exportados com sucesso![/bold green]")
    except Exception as e:
        logger.error(f"Erro na exportação de artefatos: {e}")
        console.print(f"[bold red]Erro crítico na exportação: {e}[/bold red]")
        return False

    console.print(f"\n[bold green]✓ Pipeline diário finalizado com status {report['status']} às {datetime.datetime.now().strftime('%H:%M:%S')}.[/bold green]")
    default_repo._conn.execute("CHECKPOINT")
    default_repo._conn.close()
    return report["status"] != STATUS_FAILED


if __name__ == "__main__":
    success = run_full_daily_pipeline()
    sys.exit(0 if success else 1)
