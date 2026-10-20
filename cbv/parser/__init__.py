"""Parser package for match reports and statistics."""

from cbv.parser.match_report import (
    parse_match_report_pdf,
    save_processed_match,
    extract_match_metadata,
    extract_teams,
    extract_set_scores,
)
from cbv.parser.player_stats import parse_player_row, extract_player_rows
from cbv.parser.team_stats import extract_team_totals
from cbv.parser.tactical import extract_tactical_data

__all__ = [
    "parse_match_report_pdf",
    "save_processed_match",
    "extract_match_metadata",
    "extract_teams",
    "extract_set_scores",
    "parse_player_row",
    "extract_player_rows",
    "extract_team_totals",
    "extract_tactical_data",
]

