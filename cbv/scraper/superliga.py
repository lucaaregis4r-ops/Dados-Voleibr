"""Multi-edition scraper and ingestion pipeline for CBV Superliga (Masculina & Feminina)."""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urljoin
from datetime import datetime
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from cbv.config import (
    BASE_URL,
    RAW_REPORTS_DIR,
    RAW_PAGES_DIR,
    logger,
)
from cbv.models.match import Match, SetScore
from cbv.models.stats import TeamMatchStats, MatchData
from cbv.parser.match_report import parse_match_report_pdf, normalize_team_name
from cbv.database.repository import default_repo

console = Console()

SUPERLIGA_EDITIONS: Dict[str, Dict[str, str]] = {
    "2025-2026_masculina": {
        "season": "2025-2026",
        "gender": "masculino",
        "category": "A",
        "competition": "SUPERLIGA",
        "url": f"{BASE_URL}/volei-de-quadra/2025-2026/superliga-a-masculina/sumulas",
    },
    "2025-2026_feminina": {
        "season": "2025-2026",
        "gender": "feminino",
        "category": "A",
        "competition": "SUPERLIGA",
        "url": f"{BASE_URL}/volei-de-quadra/2025-2026/superliga-a-feminina/sumulas",
    },
    "2024-2025_masculina": {
        "season": "2024-2025",
        "gender": "masculino",
        "category": "A",
        "competition": "SUPERLIGA",
        "url": f"{BASE_URL}/volei-de-quadra/2024-2025/superliga-a-masculina/sumulas",
    },
    "2024-2025_feminina": {
        "season": "2024-2025",
        "gender": "feminino",
        "category": "A",
        "competition": "SUPERLIGA",
        "url": f"{BASE_URL}/volei-de-quadra/2024-2025/superliga-a-feminina/sumulas",
    },
    "atual_feminina": {
        "season": "2026-2027",
        "gender": "feminino",
        "category": "A",
        "competition": "SUPERLIGA",
        "url": f"{BASE_URL}/volei-de-quadra/superliga-a-feminina/sumulas",
    },
}


def fetch_sumulas_table(url: str) -> List[Dict[str, Any]]:
    """
    Fetches and parses all match rows from a CBV sumulas table page.
    Returns structured list of matches with IDs, teams, scores, and document links.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Failed to fetch sumulas page {url}: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")
    parsed_matches: List[Dict[str, Any]] = []

    for r in rows:
        tds = r.find_all("td")
        if len(tds) < 8:
            continue

        date_str = tds[0].get_text(strip=True)
        home_raw = tds[1].get_text(strip=True)
        home_score_str = tds[3].get_text(strip=True)
        away_score_str = tds[5].get_text(strip=True)
        away_raw = tds[7].get_text(strip=True)

        if not home_raw or not away_raw:
            continue

        mr_a = r.find("a", href=re.compile(r"matches/.*(?<!scoresheet)\.pdf$"))
        sc_a = r.find("a", href=re.compile(r"matches/.*scoresheet\.pdf$"))
        mr_url = mr_a["href"].strip() if mr_a else None
        sc_url = sc_a["href"].strip() if sc_a else None

        # Extract match ID from document link if present
        match_id = None
        for link in [mr_url, sc_url]:
            if link:
                m = re.search(r"/matches/(\d+)-", link)
                if m:
                    match_id = int(m.group(1))
                    break

        home_sets = int(home_score_str) if home_score_str.isdigit() else None
        away_sets = int(away_score_str) if away_score_str.isdigit() else None

        parsed_matches.append({
            "match_id": match_id,
            "date_str": date_str,
            "home_team": normalize_team_name(home_raw),
            "away_team": normalize_team_name(away_raw),
            "home_sets": home_sets,
            "away_sets": away_sets,
            "match_report_url": mr_url,
            "scoresheet_url": sc_url,
        })

    return parsed_matches


def download_file(url: str, dest_path: Path, retries: int = 3) -> bool:
    """Downloads a file with retries and validation."""
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp, open(dest_path, "wb") as f:
                f.write(resp.read())
            if dest_path.stat().st_size > 0:
                return True
        except Exception as e:
            if attempt == retries - 1:
                logger.warning(f"Download failed for {url}: {e}")
    return False


def process_superliga_match(
    match_info: Dict[str, Any],
    metadata: Dict[str, Any],
    force: bool = False,
) -> Dict[str, Any]:
    """
    Downloads, parses, and persists a single Superliga match into DuckDB.
    """
    mid = match_info.get("match_id")
    if not mid:
        return {"match_id": None, "status": "skipped", "reason": "No match ID"}

    # Check if already processed
    if not force and default_repo.match_exists(mid):
        return {"match_id": mid, "status": "cached", "reason": "Already in DB"}

    mr_url = match_info.get("match_report_url")
    sc_url = match_info.get("scoresheet_url")
    competition = metadata.get("competition", "SUPERLIGA")
    category = metadata.get("category", "A")
    gender = metadata.get("gender", "masculino")

    pdf_path = RAW_REPORTS_DIR / f"{mid}.pdf"
    sc_path = RAW_REPORTS_DIR / f"{mid}_scoresheet.pdf"

    # 1. Try downloading and parsing the Match Report (contains deep player & tactical stats)
    if mr_url:
        download_file(mr_url, pdf_path)
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            try:
                data = parse_match_report_pdf(
                    pdf_path=pdf_path,
                    match_id=mid,
                    competition=competition,
                    category=category,
                    gender=gender,
                )
                # Ensure canonical teams and score from official table if needed
                if match_info.get("home_team"):
                    data.match.home_team = match_info["home_team"]
                if match_info.get("away_team"):
                    data.match.away_team = match_info["away_team"]
                if match_info.get("home_sets") is not None:
                    data.match.home_sets = match_info["home_sets"]
                if match_info.get("away_sets") is not None:
                    data.match.away_sets = match_info["away_sets"]

                default_repo.save_match_data(data)
                return {"match_id": mid, "status": "success", "mode": "match_report"}
            except Exception as e:
                logger.warning(f"Match report parse failed for {mid} ({e}), falling back to scoresheet...")

    # 2. Fallback: Save ground truth match from official table + scoresheet
    if match_info.get("home_sets") is not None:
        date_val = None
        d_str = match_info.get("date_str")
        if d_str:
            d_m = re.search(r"(\d{2}/\d{2}/\d{4})", d_str)
            if d_m:
                try:
                    date_val = datetime.strptime(d_m.group(1), "%d/%m/%Y").date()
                except ValueError:
                    pass

        time_val = None
        if d_str:
            t_m = re.search(r"(\d{2}:\d{2})", d_str)
            if t_m:
                time_val = t_m.group(1)

        fallback_match = Match(
            match_id=mid,
            date=date_val,
            time_str=time_val,
            competition=competition,
            category=category,
            gender=gender,
            home_team=match_info["home_team"],
            away_team=match_info["away_team"],
            home_sets=match_info["home_sets"],
            away_sets=match_info["away_sets"],
            validation_status="VALID",
        )

        fallback_data = MatchData(
            match=fallback_match,
            sets=[],
            players=[],
            teams=[
                TeamMatchStats(match_id=mid, team=match_info["home_team"]),
                TeamMatchStats(match_id=mid, team=match_info["away_team"]),
            ],
            tactical=None,
            validation_status="VALID",
        )
        default_repo.save_match_data(fallback_data)
        return {"match_id": mid, "status": "success", "mode": "table_fallback"}

    return {"match_id": mid, "status": "error", "reason": "Could not parse or persist match"}


def scrape_all_superliga_editions(
    editions: Optional[List[str]] = None,
    limit: Optional[int] = None,
    workers: int = 6,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Scrapes and syncs matches across specified or all Superliga editions.
    """
    target_editions = editions or list(SUPERLIGA_EDITIONS.keys())
    results_summary: Dict[str, Any] = {
        "total_discovered": 0,
        "new_ingested": 0,
        "already_cached": 0,
        "errors": 0,
        "editions_processed": {},
    }

    console.print(f"[bold cyan]🏐 Iniciando Coleta Massiva da Superliga ({len(target_editions)} edições)...[/]")

    for ed_key in target_editions:
        meta = SUPERLIGA_EDITIONS.get(ed_key)
        if not meta:
            continue

        console.print(f"\n[bold yellow]🔍 Coletando tabela: {ed_key} ({meta['url']})[/]")
        matches = fetch_sumulas_table(meta["url"])
        if limit:
            matches = matches[:limit]

        results_summary["total_discovered"] += len(matches)
        console.print(f"  • Jogos encontrados na súmula: [bold]{len(matches)}[/]")

        if not matches:
            continue

        new_count = 0
        cached_count = 0
        err_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Processando {ed_key}...", total=len(matches))

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(process_superliga_match, m, meta, force): m
                    for m in matches
                }

                for future in as_completed(futures):
                    res = future.result()
                    status = res.get("status")
                    if status == "success":
                        new_count += 1
                    elif status == "cached":
                        cached_count += 1
                    else:
                        err_count += 1
                    progress.advance(task)

        results_summary["new_ingested"] += new_count
        results_summary["already_cached"] += cached_count
        results_summary["errors"] += err_count
        results_summary["editions_processed"][ed_key] = {
            "total": len(matches),
            "new": new_count,
            "cached": cached_count,
            "errors": err_count,
        }

        console.print(
            f"  [green]✓ {ed_key}: {new_count} novos inseridos, {cached_count} em cache, {err_count} erros.[/]"
        )

    console.print(
        f"\n[bold green]🏁 Coleta Finalizada! Total inseridos: {results_summary['new_ingested']}, "
        f"Em cache: {results_summary['already_cached']}[/]"
    )
    return results_summary
