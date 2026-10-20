"""Parser functions for extracting and normalizing team-level statistics."""

from typing import Optional, List
import re
from cbv.models.stats import TeamMatchStats
from cbv.parser.player_stats import parse_int, parse_float


def extract_team_totals(lines: List[str], match_id: int, team_name: str) -> TeamMatchStats:
    """
    Extracts aggregate team statistics, coaches, and opponent errors from a team section.
    """
    full_text = "\n".join(lines)

    # 1. Coach & Assistant
    coach = None
    coach_match = re.search(r"Treinador\s+(.*?)(?:\s+Set\s+\d|\n|$)", full_text, re.IGNORECASE)
    if coach_match:
        coach = coach_match.group(1).strip()

    assistant = None
    asst_match = re.search(r"Assistente\s+(.*?)(?:\s+Set\s+\d|\n|$)", full_text, re.IGNORECASE)
    if asst_match:
        assistant = asst_match.group(1).strip()

    # 2. Opponent errors calculated from sets breakdown: "Set X Ser Atk Blo Op.Er"
    opponent_errors = 0
    found_sets = False
    for match in re.finditer(r"Set\s+\d\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", full_text, re.IGNORECASE):
        found_sets = True
        _, _, _, oper = match.groups()
        if oper.isdigit():
            opponent_errors += int(oper)

    # 3. Team totals row (line containing "otal de jogadores" or "Total de jogadores")
    # Stat tokens: 16 values
    # [tot points, bp, w-l, serve tot, serve err, serve pts, rec tot, rec err, rec pos%, rec exc%, atk tot, atk err, atk blo, atk pts, atk pts%, bk pts]
    stats_kwargs = {}
    for line in lines:
        line_s = line.strip()
        if "tal de jogadores" in line_s.lower():
            # Separate glued percentages and parentheses like '100%(100%)'
            line_s = re.sub(r"(%)\(", r"\1 (", line_s)
            line_s = re.sub(r"\)(%|\d)", r") \1", line_s)
            tokens = line_s.split()
            # Find the position where statistical tokens begin (16 tokens from right)
            if len(tokens) >= 16:

                st = tokens[-16:]
                stats_kwargs = {
                    "points_total": parse_int(st[0]),
                    "break_points": parse_int(st[1]),
                    "win_loss": parse_int(st[2]),
                    "serve_attempts": parse_int(st[3]),
                    "serve_errors": parse_int(st[4]),
                    "serve_points": parse_int(st[5]),
                    "reception_attempts": parse_int(st[6]),
                    "reception_errors": parse_int(st[7]),
                    "reception_positive_pct": parse_float(st[8]),
                    "reception_excellent_pct": parse_float(st[9]),
                    "attack_attempts": parse_int(st[10]),
                    "attack_errors": parse_int(st[11]),
                    "attack_blocked": parse_int(st[12]),
                    "attack_points": parse_int(st[13]),
                    "attack_points_pct": parse_float(st[14]),
                    "block_points": parse_int(st[15]),
                }
            break

    return TeamMatchStats(
        match_id=match_id,
        team=team_name,
        coach=coach,
        assistant=assistant,
        opponent_errors=opponent_errors if found_sets else None,
        **stats_kwargs,
    )
