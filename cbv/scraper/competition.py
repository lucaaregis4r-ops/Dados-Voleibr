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
from cbv.scraper.downloader import process_single_game, DownloadError, MatchReportNotAvailable
from cbv.database.repository import default_repo

console = Console()
FAILED_GAMES_FILE = DATA_DIR / "failed_games.json"


def normalize_category(category: str) -> str:
    """Normalizes category string (e.g. 'sub18' -> 'sub-18')."""
    cat = category.lower().strip()
    if cat.startswith("sub") and not cat.startswith("sub-"):
        return f"sub-{cat[3:]}"
    return cat


def parse_competition_url(url: str) -> Dict[str, Any]:
    """
    Parses a CBV competition URL into structured metadata.
    Handles varied formats, trailing slashes, query parameters, and missing protocols.
    """
    raw_url = url.strip()
    if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        raw_url = f"https://{raw_url}"

    from urllib.parse import urlparse
    parsed = urlparse(raw_url)
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    metadata: Dict[str, Any] = {
        "url": clean_url,
        "competition": "cbs",
        "season": 2026,
        "gender": "feminino",
        "category": "sub18",
        "division": "especial",
    }

    # Pattern: /volei-de-quadra/{competition}/{season}/{gender}/{endpoint}
    m = re.search(
        r"/volei-de-quadra/(?P<competition>[^/]+)/(?P<season>\d{4})/(?P<gender>[^/]+)/(?P<endpoint>[^/?#]+)",
        parsed.path,
        re.IGNORECASE,
    )
    if m:
        metadata["competition"] = m.group("competition").lower()
        metadata["season"] = int(m.group("season"))
        metadata["gender"] = m.group("gender").lower()
        endpoint = m.group("endpoint").lower()

        # Parse endpoint, e.g. sub-18-especial or sub-16-1-divisao
        sub_m = re.search(r"(sub[-_]?\d+)", endpoint)
        if sub_m:
            cat_raw = sub_m.group(1).replace("-", "").replace("_", "")
            metadata["category"] = cat_raw
            div_part = endpoint.replace(sub_m.group(1), "").strip("-_")
            if div_part:
                metadata["division"] = div_part
        else:
            metadata["division"] = endpoint
    else:
        yr = re.search(r"/(\d{4})/", parsed.path)
        if yr:
            metadata["season"] = int(yr.group(1))
        if "feminino" in parsed.path.lower():
            metadata["gender"] = "feminino"
        elif "masculino" in parsed.path.lower():
            metadata["gender"] = "masculino"
        sub_m = re.search(r"(sub[-_]?\d+)", parsed.path, re.IGNORECASE)
        if sub_m:
            metadata["category"] = sub_m.group(1).lower().replace("-", "").replace("_", "")

    return metadata


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
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes full competition scraping pipeline with failure tolerance:
    1. Discovers matches on competition page (via constructed or direct URL)
    2. Checks database to skip existing matches
    3. Processes each match incrementally
    4. Records failures without halting whole run
    5. Displays progress summary
    """
    if url:
        parsed_meta = parse_competition_url(url)
        comp_url = parsed_meta["url"]
        competition = parsed_meta["competition"]
        category = parsed_meta["category"]
        gender = parsed_meta["gender"]
        division = parsed_meta["division"]
        season = parsed_meta["season"]
    else:
        comp_url = build_competition_url(
            competition=competition,
            category=category,
            gender=gender,
            division=division,
            season=season,
        )

    comp_title = f"{competition.upper()} {category.upper()} {gender.upper()} {division.upper()} {season}"
    console.print(f"\n[bold]{comp_title}[/bold]")
    console.print(f"[dim]URL: {comp_url}[/dim]\n")

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
    scheduled_count = 0
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
        except MatchReportNotAvailable:
            scheduled_count += 1
            console.print(f"[{idx:02d}/{len(discovered_matches)}] {mid} [dim](agendado / aguardando súmula)[/dim]")
            continue
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
    console.print(f"  [green]VALID:     {valid_count}[/green]")
    console.print(f"  [yellow]WARNING:   {warning_count}[/yellow]")
    console.print(f"  [cyan]AGENDADOS: {scheduled_count}[/cyan]")
    console.print(f"  [red]FAILED:    {failed_count}[/red]")
    console.print(f"  [dim]SKIPPED:   {skipped_count}[/dim]\n")

    return {
        "total": len(discovered_matches),
        "valid": valid_count,
        "warning": warning_count,
        "scheduled": scheduled_count,
        "failed": failed_count,
        "skipped": skipped_count,
    }
