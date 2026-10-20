"""Competition scraping and match discovery module."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin
import json
import re
from bs4 import BeautifulSoup
from rich.console import Console

from cbv.config import BASE_URL, DATA_DIR, logger
from cbv.scraper.client import HttpClient, default_client
from cbv.scraper.downloader import process_single_game, DownloadError
from cbv.database.repository import default_repo

console = Console()
FAILED_GAMES_FILE = DATA_DIR / "failed_games.json"


def normalize_category(category: str) -> str:
    """Normalizes category string (e.g. 'sub18' -> 'sub-18')."""
    cat = category.lower().strip()
    if cat.startswith("sub") and not cat.startswith("sub-"):
        return f"sub-{cat[3:]}"
    return cat


def build_competition_url(
    competition: str = "cbs",
    category: str = "sub18",
    gender: str = "masculino",
    division: str = "especial",
    season: int = 2026,
    base_url: str = BASE_URL,
) -> str:
    """
    Constructs the canonical URL for a CBV competition page.
    Example: https://cbv.com.br/volei-de-quadra/cbs/2026/masculino/sub-18-especial
    """
    cat_clean = normalize_category(category)
    div_clean = division.lower().replace(" ", "-").strip()
    # e.g., 'sub-18-especial' or 'sub-18-primeira-divisao'
    endpoint = f"{cat_clean}-{div_clean}"
    return f"{base_url}/volei-de-quadra/{competition.lower()}/{season}/{gender.lower()}/{endpoint}"


def discover_matches(
    competition_url: str,
    client: Optional[HttpClient] = None,
) -> List[Dict[str, Any]]:
    """
    Scrapes a competition page to discover all legitimate public match IDs.
    Does not guess or increment IDs randomly.
    """
    client = client or default_client
    logger.info(f"Discovering matches from competition URL: {competition_url}")

    try:
        response = client.get(competition_url)
    except Exception as e:
        logger.error(f"Failed to fetch competition page {competition_url}: {e}")
        raise

    soup = BeautifulSoup(response.text, "lxml")
    matches: List[Dict[str, Any]] = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        m = re.search(r"/jogo/(\d+)", href)
        if m:
            match_id = int(m.group(1))
            if match_id not in seen:
                seen.add(match_id)
                full_url = urljoin(BASE_URL, f"/jogo/{match_id}")
                matches.append({
                    "match_id": match_id,
                    "url": full_url,
                })

    logger.info(f"Discovered {len(matches)} unique matches for {competition_url}")
    return matches


def save_failed_games(failed_list: List[Dict[str, Any]]) -> None:
    """Saves failed matches list to data/failed_games.json for audit and retry."""
    FAILED_GAMES_FILE.write_text(
        json.dumps(failed_list, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_failed_games() -> List[Dict[str, Any]]:
    """Loads failed matches list if available."""
    if FAILED_GAMES_FILE.exists():
        try:
            return json.loads(FAILED_GAMES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def scrape_competition(
    competition: str = "cbs",
    category: str = "sub18",
    gender: str = "masculino",
    division: str = "especial",
    season: int = 2026,
    force: bool = False,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes full competition scraping pipeline with failure tolerance:
    1. Discovers matches on competition page
    2. Checks database to skip existing matches
    3. Processes each match incrementally
    4. Records failures without halting whole run
    5. Displays progress summary
    """
    comp_title = f"{competition.upper()} {category.upper()} {gender.upper()} {division.upper()} {season}"
    console.print(f"\n[bold]{comp_title}[/bold]\n")

    comp_url = build_competition_url(
        competition=competition,
        category=category,
        gender=gender,
        division=division,
        season=season,
    )

    try:
        discovered_matches = discover_matches(comp_url)
    except Exception as e:
        console.print(f"[red]Erro ao carregar página da competição:[/red] {e}")
        return {"total": 0, "valid": 0, "warning": 0, "failed": 1, "skipped": 0}

    total_discovered = len(discovered_matches)
    console.print(f"[cyan]{total_discovered} partidas encontradas[/cyan]\n")

    if limit and limit > 0:
        discovered_matches = discovered_matches[:limit]
        console.print(f"[dim]Limitado a {len(discovered_matches)} partidas para teste[/dim]\n")

    valid_count = 0
    warning_count = 0
    failed_count = 0
    skipped_count = 0
    failed_list: List[Dict[str, Any]] = []

    for idx, match_info in enumerate(discovered_matches, start=1):
        mid = match_info["match_id"]

        # Check if already processed in database
        if not force and default_repo.match_exists(mid):
            logger.info(f"game={mid} already in database, skipping")
            console.print(f"[{idx:02d}/{len(discovered_matches)}] {mid} [dim](já processado no banco)[/dim]")
            skipped_count += 1
            continue

        try:
            res = process_single_game(mid, force=force)
            if res.get("validation_status") == "VALID":
                valid_count += 1
            else:
                warning_count += 1
        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            logger.error(f"game={mid} failed during competition scrape: {error_msg}")
            failed_list.append({"match_id": mid, "reason": error_msg})
            console.print(f"[red]✗ partida {mid} falhou: {error_msg}[/red]\n")
            continue

    save_failed_games(failed_list)

    # Print final summary
    console.print("\n[bold]Resumo da Competição:[/bold]")
    console.print(f"  [green]VALID:   {valid_count}[/green]")
    console.print(f"  [yellow]WARNING: {warning_count}[/yellow]")
    console.print(f"  [red]FAILED:  {failed_count}[/red]")
    console.print(f"  [dim]SKIPPED: {skipped_count}[/dim]\n")

    return {
        "total": len(discovered_matches),
        "valid": valid_count,
        "warning": warning_count,
        "failed": failed_count,
        "skipped": skipped_count,
    }
