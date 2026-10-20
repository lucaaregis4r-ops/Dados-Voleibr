"""Parser functions for extracting and normalizing player statistics."""

from typing import Optional, List, Any
import re
from cbv.models.player import PlayerMatchStats


def clean_val(val: Optional[str]) -> Optional[str]:
    """Cleans a raw text token, returning None if empty or dot."""
    if val is None:
        return None
    val = val.strip()
    if val in (".", "-", "", "None"):
        return None
    return val


def parse_int(val: Optional[str]) -> Optional[int]:
    """Parses an integer from a string value, handling leading signs like +3, -1."""
    cleaned = clean_val(val)
    if cleaned is None:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_float(val: Optional[str]) -> Optional[float]:
    """Parses a float from a string, supporting comma or dot decimals and percentages."""
    cleaned = clean_val(val)
    if cleaned is None:
        return None
    # Strip percent sign or parentheses
    cleaned = cleaned.replace("%", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_player_row(line: str, match_id: int, team_name: str) -> Optional[PlayerMatchStats]:
    """
    Parses a single player row string from the VolleyStation layout.
    Example:
    '01 ARTHUR            1 1    5.8 6 5 +3  17 3 5  . .  .  .   1 .  . 1 100% .'
    '03 L RAFAEL                 5.5 . .  .  . . .  21 . 67% (38%) . . . . .  .'
    """
    line_s = line.strip()
    if len(line_s) < 3 or not line_s[:2].isdigit():
        return None

    # Separate glued percentages and parentheses like '100%(100%)'
    line_s = re.sub(r"(%)\(", r"\1 (", line_s)
    line_s = re.sub(r"\)(%|\d)", r") \1", line_s)

    tokens = line_s.split()
    # A valid player stats line has at least 17 statistical tokens on the right
    if len(tokens) < 18:
        return None


    stat_tokens = tokens[-17:]
    left_tokens = tokens[:-17]

    try:
        player_number = int(left_tokens[0])
    except ValueError:
        return None

    idx = 1
    is_libero = False
    if len(left_tokens) > idx and left_tokens[idx].upper() == "L":
        is_libero = True
        idx += 1

    # Extract starting positions in sets (trailing digits in left_tokens)
    remaining = left_tokens[idx:]
    sets: List[str] = []
    while remaining and (remaining[-1].isdigit() or remaining[-1] in ("*", "▲")):
        sets.insert(0, remaining.pop())

    player_name = " ".join(remaining)

    # Stat tokens:
    # 0: rating
    # 1: tot points, 2: bp, 3: w-l
    # 4: serve tot, 5: serve err, 6: serve pts
    # 7: rec tot, 8: rec err, 9: rec pos%, 10: rec exc%
    # 11: atk tot, 12: atk err, 13: atk blo, 14: atk pts, 15: atk pts%
    # 16: bk pts
    return PlayerMatchStats(
        match_id=match_id,
        team=team_name,
        player_number=player_number,
        player_name=player_name,
        is_libero=is_libero,
        starting_positions=sets,
        rating=parse_float(stat_tokens[0]),
        points_total=parse_int(stat_tokens[1]),
        break_points=parse_int(stat_tokens[2]),
        win_loss=parse_int(stat_tokens[3]),
        serve_attempts=parse_int(stat_tokens[4]),
        serve_errors=parse_int(stat_tokens[5]),
        serve_points=parse_int(stat_tokens[6]),
        reception_attempts=parse_int(stat_tokens[7]),
        reception_errors=parse_int(stat_tokens[8]),
        reception_positive_pct=parse_float(stat_tokens[9]),
        reception_excellent_pct=parse_float(stat_tokens[10]),
        attack_attempts=parse_int(stat_tokens[11]),
        attack_errors=parse_int(stat_tokens[12]),
        attack_blocked=parse_int(stat_tokens[13]),
        attack_points=parse_int(stat_tokens[14]),
        attack_points_pct=parse_float(stat_tokens[15]),
        block_points=parse_int(stat_tokens[16]),
    )


def extract_player_rows(lines: List[str], match_id: int, team_name: str) -> List[PlayerMatchStats]:
    """Extracts all player rows for a team section."""
    players: List[PlayerMatchStats] = []
    for line in lines:
        line_clean = line.strip()
        if len(line_clean) > 2 and line_clean[:2].isdigit():
            player = parse_player_row(line_clean, match_id, team_name)
            if player:
                players.append(player)
    return players
