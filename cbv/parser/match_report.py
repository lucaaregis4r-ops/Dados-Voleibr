"""Match Report parser coordinating PDF reading, extraction, and validation."""

from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Tuple
import json
import re
import pdfplumber

from cbv.__init__ import PARSER_VERSION
from cbv.config import PROCESSED_DIR, logger
from cbv.models.match import Match, SetScore
from cbv.models.player import PlayerMatchStats
from cbv.models.stats import TeamMatchStats, MatchData
from cbv.parser.player_stats import extract_player_rows
from cbv.parser.team_stats import extract_team_totals
from cbv.validation.match_validator import MatchValidator


def extract_match_metadata(text: str, match_id: int) -> Tuple[Optional[date], Optional[str], Optional[str]]:
    """Extracts date, time and competition from header text."""
    date_val = None
    date_m = re.search(r"Data\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if not date_m:
        date_m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if date_m:
        try:
            date_val = datetime.strptime(date_m.group(1), "%d/%m/%Y").date()
        except ValueError:
            pass

    time_val = None
    time_m = re.search(r"Hora\s+(\d{2}:\d{2})", text, re.IGNORECASE)
    if time_m:
        time_val = time_m.group(1)

    competition = None
    if "CBS" in text:
        competition = "CBS"
    elif "SUPERLIGA" in text.upper():
        competition = "SUPERLIGA"

    return date_val, time_val, competition


BRAZILIAN_STATES = [
    "ACRE", "ALAGOAS", "AMAPÁ", "AMAZONAS", "BAHIA", "CEARÁ",
    "DISTRITO FEDERAL", "ESPÍRITO SANTO", "GOIÁS", "MARANHÃO",
    "MATO GROSSO", "MATO GROSSO DO SUL", "MINAS GERAIS", "PARÁ",
    "PARAÍBA", "PARANÁ", "PERNAMBUCO", "PIAUÍ", "RIO DE JANEIRO",
    "RIO GRANDE DO NORTE", "RIO GRANDE DO SUL", "RONDÔNIA",
    "RORAIMA", "SANTA CATARINA", "SÃO PAULO", "SERGIPE", "TOCANTINS"
]


def normalize_team_name(name: str) -> str:
    """Normalizes team names, repairing encoding issues like 'MARANH?O' -> 'MARANHÃO'."""
    import unicodedata

    name_clean = name.strip()
    if "?" in name_clean:
        pattern = "^" + re.escape(name_clean).replace(r"\?", ".") + "$"
        for state in BRAZILIAN_STATES:
            unacc = "".join(c for c in unicodedata.normalize("NFD", state) if unicodedata.category(c) != "Mn")
            if re.match(pattern, state, re.IGNORECASE) or re.match(pattern, unacc, re.IGNORECASE):
                return state
    return name_clean


def extract_teams(lines: List[str]) -> Tuple[str, str, str, str, Optional[int], Optional[int]]:
    """
    Extracts raw and normalized home/away teams, and sets won from header lines.
    Returns: (raw_home, raw_away, norm_home, norm_away, home_sets, away_sets)
    """
    for line in lines[:15]:
        line_clean = line.strip()
        # Look for [TEAM_A] [SETS_A] [SETS_B] [TEAM_B]
        m = re.search(r"([^\d\n]{3,})\s+(\d+)\s+(\d+)\s+([^\d\n]{3,})$", line_clean)
        if m:
            raw_home = m.group(1).strip()
            home_sets = int(m.group(2))
            away_sets = int(m.group(3))
            raw_away = m.group(4).strip()
            # Verify this is not a table header
            if "SET" not in raw_home.upper() and "PONTOS" not in raw_home.upper():
                norm_home = normalize_team_name(raw_home)
                norm_away = normalize_team_name(raw_away)
                return raw_home, raw_away, norm_home, norm_away, home_sets, away_sets

    raise ValueError("Não foi possível identificar equipes e placar no cabeçalho do relatório.")



def extract_set_scores(lines: List[str], match_id: int) -> List[SetScore]:
    """Extracts individual set durations, partials, and final scores."""
    sets: List[SetScore] = []
    # Search header area (first 15 lines)
    for line in lines[:15]:
        # Matches e.g.: '  1  00:25 1-8 8-16 13-21 19-25' or '2  -1:49 7-8 10-16 14-21 21-25'
        m = re.search(r"(?:^|\s+)(\d)\s+([-+]?\d+:\d{2})?\s*(.*?)(?:(\d+)-(\d+))\s*$", line)
        if m:
            set_num = int(m.group(1))
            duration_str = m.group(2)
            partials = m.group(3).strip()
            home_pts = int(m.group(4))
            away_pts = int(m.group(5))

            duration_min = None
            if duration_str:
                try:
                    # Clean sign if negative or anomalous
                    clean_dur = duration_str.lstrip("+-")
                    parts = clean_dur.split(":")
                    duration_min = int(parts[0]) * 60 + int(parts[1])
                except (ValueError, IndexError):
                    pass

            sets.append(
                SetScore(
                    match_id=match_id,
                    set_number=set_num,
                    home_points=home_pts,
                    away_points=away_pts,
                    duration_minutes=duration_min,
                    partial_scores=partials if partials else None,
                )
            )


    # Sort by set number
    sets.sort(key=lambda s: s.set_number)
    return sets


def parse_match_report_pdf(pdf_path: Path, match_id: int) -> MatchData:
    """
    Parses a Match Report PDF into structured MatchData with validation.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Relatório PDF não encontrado em {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError(f"PDF {pdf_path} não contém páginas")
        # Extract formatted layout text
        layout_text = pdf.pages[0].extract_text(layout=True)

    lines = layout_text.split("\n")

    # 1. Metadata & Teams
    match_date, match_time, competition = extract_match_metadata(layout_text, match_id)
    raw_home, raw_away, home_team, away_team, home_sets, away_sets = extract_teams(lines)

    # 2. Set Scores
    sets = extract_set_scores(lines, match_id)

    # 3. Locate Team Sections
    home_idx = None
    away_idx = None
    footer_idx = None

    for i, line in enumerate(lines):
        clean = line.strip()
        if (clean in (raw_home, home_team)) and i > 5 and home_idx is None:
            home_idx = i
        elif (clean in (raw_away, away_team)) and home_idx is not None and away_idx is None:
            away_idx = i
        elif "BP Break point" in line and away_idx is not None:
            footer_idx = i
            break

    if home_idx is None or away_idx is None:
        raise ValueError(f"Não foi possível delimitar seções das equipes ({home_team}, {away_team}) no PDF.")

    home_lines = lines[home_idx:away_idx]
    away_lines = lines[away_idx:footer_idx if footer_idx else len(lines)]


    # 4. Extract Players
    home_players = extract_player_rows(home_lines, match_id, home_team)
    away_players = extract_player_rows(away_lines, match_id, away_team)
    all_players = home_players + away_players

    # 5. Extract Team Totals
    home_totals = extract_team_totals(home_lines, match_id, home_team)
    away_totals = extract_team_totals(away_lines, match_id, away_team)
    all_teams = [home_totals, away_totals]

    # Assemble Match
    match_model = Match(
        match_id=match_id,
        date=match_date,
        time_str=match_time,
        competition=competition,
        category="sub18",  # Default or derived
        gender="masculino",
        home_team=home_team,
        away_team=away_team,
        home_sets=home_sets,
        away_sets=away_sets,
    )

    match_data = MatchData(
        match=match_model,
        sets=sets,
        players=all_players,
        teams=all_teams,
        parser_version=PARSER_VERSION,
    )

    # 6. Validation
    status, warnings = MatchValidator.validate(match_data)
    match_data.validation_status = status
    match_data.validation_warnings = warnings
    match_data.match.validation_status = status

    logger.info(
        f"game={match_id} parsed {len(all_players)} players, "
        f"{len(sets)} sets, status={status}, warnings={len(warnings)}"
    )

    return match_data


def save_processed_match(data: MatchData) -> Path:
    """Saves MatchData to data/processed/{match_id}.json."""
    output_path = PROCESSED_DIR / f"{data.match.match_id}.json"
    data_dict = data.model_dump(mode="json")
    output_path.write_text(json.dumps(data_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"game={data.match.match_id} saved JSON to {output_path}")
    return output_path
