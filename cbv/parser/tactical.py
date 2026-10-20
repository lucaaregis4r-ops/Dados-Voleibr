"""Tactical parser for extracting advanced volleyball metrics from Match Reports."""

from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import re
import pdfplumber

from cbv.config import logger
from cbv.models.tactical import (
    PhaseAttackStats,
    SideOutBreakPointStats,
    SetTacticalStats,
    TeamTacticalStats,
    MatchTacticalData,
)
from cbv.parser.player_stats import parse_int, parse_float


def parse_so_bp_cell(cell_text: str, team_name: str) -> SideOutBreakPointStats:
    """Extracts Side-Out and Break Point data from a table cell."""
    rec = re.search(r"Recepção\s+(\d+)", cell_text)
    so = re.search(r"Pontos SO\s+(\d+)", cell_text)
    so_rate = re.search(r"Cada\s+([\d\.]+)\s+recepções", cell_text)
    saque = re.search(r"Saque\s+(\d+)", cell_text)
    bp = re.search(r"Pontos BP\s+(\d+)", cell_text)
    bp_rate = re.search(r"Cada\s+([\d\.]+)\s+serviço", cell_text)

    return SideOutBreakPointStats(
        team=team_name,
        receptions_total=int(rec.group(1)) if rec else 0,
        sideout_points=int(so.group(1)) if so else 0,
        sideout_rate=float(so_rate.group(1)) if so_rate else None,
        serves_total=int(saque.group(1)) if saque else 0,
        breakpoint_points=int(bp.group(1)) if bp else 0,
        breakpoint_rate=float(bp_rate.group(1)) if bp_rate else None,
    )


def parse_rotations_cell(cell_text: str) -> Dict[str, int]:
    """Extracts point differentials for setter rotations P1 through P6."""
    rotations: Dict[str, int] = {}
    if not cell_text:
        return rotations

    for line in cell_text.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) == 2 and parts[0].isdigit():
            rot_num = int(parts[0])
            if 1 <= rot_num <= 6:
                try:
                    rotations[f"p{rot_num}"] = int(parts[1])
                except ValueError:
                    pass
    return rotations


def parse_attack_phase_row(row: List[Any], phase_name: str) -> Tuple[PhaseAttackStats, PhaseAttackStats]:
    """
    Parses attack metrics for a specific tactical phase:
    Tokens layout:
    Home: [errors, blocked, pts%, attempts]
    Away: [attempts, pts%, blocked, errors]
    """
    cells = [c for c in row if c is not None and str(c).strip()]
    num_tokens = []
    for c in cells:
        for token in str(c).split():
            if any(ch.isdigit() for ch in token):
                num_tokens.append(token)

    if len(num_tokens) >= 8:
        h_att = int(num_tokens[3])
        h_pct = float(num_tokens[2].replace("%", ""))
        h_pts = round(h_att * (h_pct / 100.0))
        h_err = int(num_tokens[0])
        h_blo = int(num_tokens[1])
        h_eff = round(((h_pts - h_err - h_blo) / h_att) * 100, 2) if h_att > 0 else None

        a_att = int(num_tokens[4])
        a_pct = float(num_tokens[5].replace("%", ""))
        a_pts = round(a_att * (a_pct / 100.0))
        a_blo = int(num_tokens[6])
        a_err = int(num_tokens[7])
        a_eff = round(((a_pts - a_err - a_blo) / a_att) * 100, 2) if a_att > 0 else None

        home_phase = PhaseAttackStats(
            phase_name=phase_name,
            attempts=h_att,
            points=h_pts,
            points_pct=h_pct,
            blocked=h_blo,
            errors=h_err,
            efficiency_pct=h_eff,
        )
        away_phase = PhaseAttackStats(
            phase_name=phase_name,
            attempts=a_att,
            points=a_pts,
            points_pct=a_pct,
            blocked=a_blo,
            errors=a_err,
            efficiency_pct=a_eff,
        )
        return home_phase, away_phase

    # Default empty stats if structure differs
    return PhaseAttackStats(phase_name=phase_name), PhaseAttackStats(phase_name=phase_name)


def parse_set_tactical_breakdowns(lines: List[str], match_id: int, team_name: str) -> List[SetTacticalStats]:
    """Extracts set-by-set skills and point generation breakdown."""
    sets_data: List[SetTacticalStats] = []
    for line in lines:
        line_clean = re.sub(r"(%)\(", r"\1 (", line)
        line_clean = re.sub(r"\)(%|\d)", r") \1", line_clean)
        m = re.search(r"Set\s+(\d)\s+(.*)", line_clean)
        if m:
            set_num = int(m.group(1))
            tokens = m.group(2).split()
            if len(tokens) >= 16:
                sets_data.append(
                    SetTacticalStats(
                        match_id=match_id,
                        team=team_name,
                        set_number=set_num,
                        serve_points_won=parse_int(tokens[0]) or 0,
                        attack_points_won=parse_int(tokens[1]) or 0,
                        block_points_won=parse_int(tokens[2]) or 0,
                        opponent_errors_won=parse_int(tokens[3]) or 0,
                        serve_total=parse_int(tokens[4]) or 0,
                        serve_errors=parse_int(tokens[5]) or 0,
                        serve_aces=parse_int(tokens[6]) or 0,
                        reception_total=parse_int(tokens[7]) or 0,
                        reception_errors=parse_int(tokens[8]) or 0,
                        reception_positive_pct=parse_float(tokens[9]),
                        reception_excellent_pct=parse_float(tokens[10]),
                        attack_total=parse_int(tokens[11]) or 0,
                        attack_errors=parse_int(tokens[12]) or 0,
                        attack_blocked=parse_int(tokens[13]) or 0,
                        attack_points=parse_int(tokens[14]) or 0,
                        attack_points_pct=parse_float(tokens[15]),
                    )
                )
    return sets_data


def extract_tactical_data(
    pdf_path: Path,
    match_id: int,
    home_team: str,
    away_team: str,
    home_lines: List[str],
    away_lines: List[str],
) -> Optional[MatchTacticalData]:
    """
    Extracts complete tactical intelligence from PDF:
    - Side-Out and Break Point rates
    - Setter rotations P1-P6 differentials
    - Phase attack execution (K1+, K1-, K2)
    - Set-by-set skills distribution
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            tactical_table = None
            for t in pdf.pages[0].extract_tables():
                if len(t) == 9 and any("1º Ataque" in str(cell) for row in t for cell in row):
                    tactical_table = t
                    break

            if not tactical_table:
                logger.warning(f"game={match_id} tactical table not located in PDF")
                return None

            # 1. SO & BP
            so_cells = [c for c in tactical_table[1] if c and "Pontos SO" in c]
            if len(so_cells) >= 2:
                home_so = parse_so_bp_cell(so_cells[0], home_team)
                away_so = parse_so_bp_cell(so_cells[1], away_team)
            else:
                home_so = SideOutBreakPointStats(team=home_team)
                away_so = SideOutBreakPointStats(team=away_team)

            # 2. Rotations
            rot_cells = [
                c for c in tactical_table[3]
                if c and any(c.strip().startswith(d) for d in ["1", "2", "3", "4", "5", "6"])
            ]
            home_rotations = parse_rotations_cell(rot_cells[0]) if rot_cells else {}
            away_rotations = parse_rotations_cell(rot_cells[-1]) if len(rot_cells) >= 2 else {}

            # 3. Phase Attack (K1+, K1-, K2)
            h_k1_pos, a_k1_pos = parse_attack_phase_row(tactical_table[4], "k1_positive_reception")
            h_k1_neg, a_k1_neg = parse_attack_phase_row(tactical_table[6], "k1_negative_reception")
            h_k2, a_k2 = parse_attack_phase_row(tactical_table[8], "k2_transition")

            # 4. Set-by-set skills
            home_set_tactics = parse_set_tactical_breakdowns(home_lines, match_id, home_team)
            away_set_tactics = parse_set_tactical_breakdowns(away_lines, match_id, away_team)

            home_team_tactics = TeamTacticalStats(
                match_id=match_id,
                team=home_team,
                sideout=home_so,
                rotations=home_rotations,
                positive_reception_attack=h_k1_pos,
                negative_reception_attack=h_k1_neg,
                transition_attack=h_k2,
                set_breakdowns=home_set_tactics,
            )

            away_team_tactics = TeamTacticalStats(
                match_id=match_id,
                team=away_team,
                sideout=away_so,
                rotations=away_rotations,
                positive_reception_attack=a_k1_pos,
                negative_reception_attack=a_k1_neg,
                transition_attack=a_k2,
                set_breakdowns=away_set_tactics,
            )

            logger.info(f"game={match_id} tactical intelligence parsed successfully")
            return MatchTacticalData(
                match_id=match_id,
                home_team=home_team,
                away_team=away_team,
                home_tactics=home_team_tactics,
                away_tactics=away_team_tactics,
            )

    except Exception as e:
        logger.error(f"game={match_id} error parsing tactical stats: {e}")
        return None
