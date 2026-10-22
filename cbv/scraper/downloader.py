"""Downloader and coordinator for match reports."""

from pathlib import Path
from typing import Optional
from rich.console import Console

from cbv.config import (
    RAW_REPORTS_DIR,
    logger,
)
from cbv.scraper.client import HttpClient, default_client
from cbv.scraper.game_page import fetch_game_page, extract_match_report_url, extract_game_links

console = Console()


class DownloadError(Exception):
    """Custom exception raised during download and validation failures."""
    pass


class MatchReportNotAvailable(DownloadError):
    """Raised when match report is not yet published (scheduled or in-progress match)."""
    pass


def get_report_cache_path(game_id: int) -> Path:
    """Returns local path for stored PDF report."""
    return RAW_REPORTS_DIR / f"{game_id}.pdf"


def validate_pdf_bytes(content: bytes) -> bool:
    """Validates that downloaded content is a non-empty valid PDF with %PDF signature."""
    if not content or len(content) == 0:
        return False
    # Check for PDF magic bytes at the start (ignoring leading whitespace/BOM if any)
    stripped = content.lstrip()
    return stripped.startswith(b"%PDF")


def download_match_report(
    game_id: int,
    report_url: str,
    force: bool = False,
    client: Optional[HttpClient] = None,
) -> Path:
    """
    Downloads and validates the Match Report PDF.
    Validates: HTTP status, content size > 0, and %PDF signature.
    """
    pdf_path = get_report_cache_path(game_id)

    if not force and pdf_path.exists():
        # Validate existing cached file
        content = pdf_path.read_bytes()
        if validate_pdf_bytes(content):
            logger.info(f"game={game_id} pdf loaded from cache: {pdf_path}")
            return pdf_path

    client = client or default_client
    logger.info(f"game={game_id} downloading report from {report_url}")

    try:
        content = client.download(report_url)
    except Exception as e:
        logger.error(f"game={game_id} failed to download report from {report_url}: {e}")
        raise DownloadError(f"Erro ao baixar PDF de {report_url}: {e}") from e

    if not validate_pdf_bytes(content):
        logger.error(f"game={game_id} downloaded content is not a valid PDF (size={len(content)} bytes)")
        raise DownloadError(f"Arquivo baixado para o jogo {game_id} não é um PDF válido.")

    pdf_path.write_bytes(content)
    logger.info(f"game={game_id} pdf downloaded and validated ({len(content)} bytes)")
    return pdf_path


def process_single_game(game_id: int, force: bool = False) -> dict:
    """
    Executes end-to-end workflow for a single game:
    1. Fetch game page
    2. Extract Match Report URL
    3. Download & validate PDF report
    4. Parse match report into structured data
    5. Validate numerical and structural integrity
    6. Save processed JSON
    7. Save into DuckDB database
    """
    from cbv.parser.match_report import parse_match_report_pdf, save_processed_match
    from cbv.database.repository import default_repo

    console.print(f"\n[bold]Game {game_id}[/bold]\n")

    try:
        html, was_cached = fetch_game_page(game_id, force=force)
        cache_note = " (em cache)" if was_cached else ""
        console.print(f"[green]✓[/green] página CBV acessada{cache_note}")
    except Exception as e:
        logger.error(f"game={game_id} error accessing page: {e}")
        console.print(f"[red]✗[/red] falha ao acessar página CBV: {e}")
        raise

    links = extract_game_links(html)
    report_url = links.get("match_report_url")

    if not report_url:
        logger.info(f"game={game_id} match report not available yet (scheduled/in-progress)")
        console.print("[dim]ℹ Match Report ainda não disponibilizado pela CBV (jogo agendado ou em andamento)[/dim]")
        raise MatchReportNotAvailable(f"Match Report não disponível para o jogo {game_id}")

    console.print(f"[green]✓[/green] Match Report encontrado")

    try:
        pdf_path = download_match_report(game_id, report_url, force=force)
        console.print("[green]✓[/green] PDF validado")
        console.print(f"[green]✓[/green] salvo em [bold]data/raw/reports/{game_id}.pdf[/bold]")
    except Exception as e:
        logger.error(f"game={game_id} report download/validation failed: {e}")
        console.print(f"[red]✗[/red] falha na validação/download do PDF: {e}")
        raise

    # 4. Parse & Validate
    try:
        match_data = parse_match_report_pdf(pdf_path, game_id)
        console.print(f"[green]✓[/green] {len(match_data.players)} atletas extraídos")

        status_color = "green" if match_data.validation_status == "VALID" else "yellow"
        console.print(f"[{status_color}]✓[/{status_color}] validado ({match_data.validation_status})")
        if match_data.validation_warnings:
            for w in match_data.validation_warnings:
                console.print(f"   [yellow]⚠ {w}[/yellow]")

        # 5. Save JSON
        json_path = save_processed_match(match_data)
        console.print(f"[green]✓[/green] salvo em [bold]data/processed/{game_id}.json[/bold]")

        # 6. Save DuckDB
        default_repo.save_match_data(match_data)
        console.print(f"[green]✓[/green] salvo no DuckDB ([bold]data/cbv.duckdb[/bold])\n")
    except Exception as e:
        logger.error(f"game={game_id} parsing/saving failed: {e}")
        console.print(f"[red]✗[/red] falha ao processar relatório: {e}")
        raise

    return {
        "game_id": game_id,
        "page_cached": was_cached,
        "report_url": report_url,
        "pdf_path": str(pdf_path),
        "json_path": str(json_path),
        "validation_status": match_data.validation_status,
        "player_count": len(match_data.players),
    }

