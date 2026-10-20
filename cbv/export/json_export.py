"""JSON export engine for CBV matches, players, teams, and rankings."""

from pathlib import Path
import json
from rich.console import Console

from cbv.config import BASE_DIR, logger
from cbv.database.repository import default_repo
from cbv.analysis.rankings import (
    get_scoring_ranking,
    get_attack_ranking,
    get_block_ranking,
    get_serve_ranking,
)

console = Console()
EXPORTS_DIR = BASE_DIR / "exports"


def export_all_to_json(target_dir: Path = EXPORTS_DIR) -> Path:
    """Exports structured database data and rankings to JSON files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting data to JSON in {target_dir}")

    with default_repo.get_connection() as conn:
        matches = conn.execute("SELECT * FROM matches ORDER BY match_id").fetchdf().to_dict(orient="records")
        # Convert date and timestamp objects to strings
        for m in matches:
            for k, v in m.items():
                if hasattr(v, "isoformat"):
                    m[k] = v.isoformat()

        players = conn.execute("SELECT * FROM player_match_stats ORDER BY match_id, team, player_number").fetchdf().to_dict(orient="records")
        teams = conn.execute("SELECT * FROM team_match_stats ORDER BY match_id, team").fetchdf().to_dict(orient="records")

    (target_dir / "matches.json").write_text(json.dumps(matches, indent=2, ensure_ascii=False), encoding="utf-8")
    (target_dir / "players.json").write_text(json.dumps(players, indent=2, ensure_ascii=False), encoding="utf-8")
    (target_dir / "teams.json").write_text(json.dumps(teams, indent=2, ensure_ascii=False), encoding="utf-8")

    rankings_payload = {
        "scoring": get_scoring_ranking(limit=50),
        "attack": get_attack_ranking(min_attempts=10, limit=50),
        "serve": get_serve_ranking(min_attempts=10, limit=50),
        "block": get_block_ranking(limit=50),
    }
    (target_dir / "rankings.json").write_text(json.dumps(rankings_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    console.print(f"[green]✓ Exportação JSON concluída com sucesso em [bold]{target_dir}[/bold][/green]")
    return target_dir
