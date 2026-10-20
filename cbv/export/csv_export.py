"""CSV export engine for CBV matches, players, teams, and rankings."""

from pathlib import Path
from typing import Optional
import pandas as pd
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


def export_all_to_csv(target_dir: Path = EXPORTS_DIR) -> Path:
    """Exports all DuckDB tables and computed rankings to CSV files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting tables to CSV in {target_dir}")

    with default_repo.get_connection() as conn:
        # 1. Matches
        df_matches = conn.execute("SELECT * FROM matches ORDER BY match_id").fetchdf()
        df_matches.to_csv(target_dir / "matches.csv", index=False, encoding="utf-8")

        # 2. Players
        df_players = conn.execute("SELECT * FROM player_match_stats ORDER BY match_id, team, player_number").fetchdf()
        df_players.to_csv(target_dir / "players.csv", index=False, encoding="utf-8")

        # 3. Teams
        df_teams = conn.execute("SELECT * FROM team_match_stats ORDER BY match_id, team").fetchdf()
        df_teams.to_csv(target_dir / "teams.csv", index=False, encoding="utf-8")

        # 4. Tactical Teams
        df_tac_teams = conn.execute("SELECT * FROM team_tactical_stats ORDER BY match_id, team").fetchdf()
        df_tac_teams.to_csv(target_dir / "tactical_teams.csv", index=False, encoding="utf-8")

        # 5. Tactical Sets
        df_tac_sets = conn.execute("SELECT * FROM set_tactical_stats ORDER BY match_id, team, set_number").fetchdf()
        df_tac_sets.to_csv(target_dir / "tactical_sets.csv", index=False, encoding="utf-8")


    # 4. Computed Player Rankings
    scoring = pd.DataFrame(get_scoring_ranking(limit=50))
    scoring.to_csv(target_dir / "rankings_scoring.csv", index=False, encoding="utf-8")

    attack = pd.DataFrame(get_attack_ranking(min_attempts=10, limit=50))
    attack.to_csv(target_dir / "rankings_attack.csv", index=False, encoding="utf-8")

    serve = pd.DataFrame(get_serve_ranking(min_attempts=10, limit=50))
    serve.to_csv(target_dir / "rankings_serve.csv", index=False, encoding="utf-8")

    block = pd.DataFrame(get_block_ranking(limit=50))
    block.to_csv(target_dir / "rankings_block.csv", index=False, encoding="utf-8")

    # 5. Computed Tactical Rankings & Summaries
    from cbv.analysis.tactics import get_competition_tactical_summary
    tac_summary = get_competition_tactical_summary()
    tac_summary["sideout_breakpoint"].to_csv(target_dir / "rankings_tactical_so_bp.csv", index=False, encoding="utf-8")
    tac_summary["phase_attacks"].to_csv(target_dir / "rankings_tactical_phase_attacks.csv", index=False, encoding="utf-8")
    tac_summary["rotations"].to_csv(target_dir / "rankings_tactical_rotations.csv", index=False, encoding="utf-8")
    tac_summary["reception_targets"].to_csv(target_dir / "rankings_tactical_reception_targets.csv", index=False, encoding="utf-8")
    tac_summary["offensive_usage"].to_csv(target_dir / "rankings_tactical_offensive_usage.csv", index=False, encoding="utf-8")

    console.print(f"[green]✓ Exportação CSV concluída com sucesso em [bold]{target_dir}[/bold][/green]")
    return target_dir
