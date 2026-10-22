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


CANONICAL_TEAMS = {
    "SADA CRUZEIRO": "SADA CRUZEIRO VÔLEI",
    "SADA CRUZEIRO VÔLEI": "SADA CRUZEIRO VÔLEI",
    "SESI BAURU": "SESI VÔLEI BAURU",
    "SESI VOLEI BAURU": "SESI VÔLEI BAURU",
    "SESI VÔLEI BAURU": "SESI VÔLEI BAURU",
    "DENTIL / PRAIA CLUBE": "DENTIL PRAIA CLUBE",
    "DENTIL PRAIA CLUBE": "DENTIL PRAIA CLUBE",
    "PRAIA CLUBE": "DENTIL PRAIA CLUBE",
    "PRAIA CLUBE UBERLÂNDIA …": "PRAIA CLUBE UBERLÂNDIA",
    "PRAIA CLUBE UBERLÂNDIA VOLEI": "PRAIA CLUBE UBERLÂNDIA",
    "BRASILIA VOLEI": "BRASÍLIA VÔLEI",
    "BRASÍLIA VÔLEI": "BRASÍLIA VÔLEI",
    "BRASÍLIA VÔLEI / BRB": "BRASÍLIA VÔLEI",
    "VOLEI RENATA": "VÔLEI RENATA",
    "VÔLEI RENATA": "VÔLEI RENATA",
    "SUZANO VOLEI": "SUZANO VÔLEI",
    "SUZANO VÔLEI": "SUZANO VÔLEI",
    "SANEAGO GOIÁS VOLEI": "SANEAGO GOIÁS VÔLEI",
    "SANEAGO GOIÁS VÔLEI": "SANEAGO GOIÁS VÔLEI",
    "OSASCO S?O CRISTÓV?O SAÚDE": "OSASCO SÃO CRISTÓVÃO SAÚDE",
    "OSASCO S?O CRISTÓV?O SA…": "OSASCO SÃO CRISTÓVÃO SAÚDE",
    "OSASCO SÃO CRISTÓVÃO SAÚDE": "OSASCO SÃO CRISTÓVÃO SAÚDE",
    "OSASCO": "OSASCO SÃO CRISTÓVÃO SAÚDE",
    "FLUMINENSE": "FLUMINENSE",
    "FLUMINENSE F.C": "FLUMINENSE",
    "FLUMINENSE F.C.": "FLUMINENSE",
    "JF VÔLEI": "JF VÔLEI",
    "JFVÔLEI": "JF VÔLEI",
    "VIAPOL VOLEI SAO JOSE": "VIAPOL VÔLEI SÃO JOSÉ",
    "VIAPOL VÔLEI S?O JOSÉ": "VIAPOL VÔLEI SÃO JOSÉ",
    "VIAPOL VÔLEI SÃO JOSÉ": "VIAPOL VÔLEI SÃO JOSÉ",
    "AZULIM SICOOB ARACOOP": "AZULIM SICOOB ARACOOP",
    "AZULIM SICOOB ARACOOP …": "AZULIM SICOOB ARACOOP",
    "VOLEI GUARULHOS BATEUB…": "VEDACIT VÔLEI GUARULHOS",
    "VÔLEI GUARULHOS BATEUB…": "VEDACIT VÔLEI GUARULHOS",
    "VOLEI GUARULHOS BATEUBET": "VEDACIT VÔLEI GUARULHOS",
    "VEDACIT VOLEI GUARULHOS": "VEDACIT VÔLEI GUARULHOS",
    "VEDACIT VÔLEI GUARULHOS": "VEDACIT VÔLEI GUARULHOS",
    "FLOR DE YP? PAULISTANO B…": "FLOR DE YPÊ PAULISTANO BARUERI",
    "FLOR DE YPÊ PAULISTANO BARUERI": "FLOR DE YPÊ PAULISTANO BARUERI",
    "PAULISTANO BARUERI": "FLOR DE YPÊ PAULISTANO BARUERI",
    "PAULISTANO  BARUERI": "FLOR DE YPÊ PAULISTANO BARUERI",
    "TIJUCA T?NIS CLUBE": "TIJUCA TÊNIS CLUBE",
    "TIJUCA TENIS CLUBE": "TIJUCA TÊNIS CLUBE",
    "TIJUCA TÊNIS CLUBE": "TIJUCA TÊNIS CLUBE",
    "UNILIFE MARINGA": "UNILIFE MARINGÁ",
    "UNILIFE MARINGÁ": "UNILIFE MARINGÁ",
    "SANCOR SEGUROS VOLEI": "SANCOR SEGUROS VÔLEI",
    "SANCOR SEGUROS VÔLEI": "SANCOR SEGUROS VÔLEI",
    "BRUSQUE VÔLEI": "ABEL MODA BRUSQUE VÔLEI",
    "BRUSQUE VOLEI": "ABEL MODA BRUSQUE VÔLEI",
    "ABEL MODA VOLEI": "ABEL MODA BRUSQUE VÔLEI",
    "APAN Roll on": "APAN ROLL-ON BLUMENAU",
    "APAN ROLL-ON BLUMENAU": "APAN ROLL-ON BLUMENAU",
    "GERDAU MINAS": "GERDAU MINAS",
    "ITAMBÉ MINAS": "ITAMBÉ MINAS",
    "SESC RJ FLAMENGO": "SESC RJ FLAMENGO",
    "BATAVO MACKENZIE": "BATAVO MACKENZIE",
    "E.C. PINHEIROS": "E.C. PINHEIROS",
    "RENASCE SOROCABA": "RENASCE SOROCABA",
    "NEUROLOGIA ATIVA": "NEUROLOGIA ATIVA",
    "JOINVILLE VÔLEI": "JOINVILLE VÔLEI",
}


def normalize_team_name(name: str) -> str:
    """Normalizes team names to canonical representations, repairing encodings and prefixes."""
    import unicodedata

    name_clean = name.strip()
    name_clean = name_clean.replace("S?O", "SÃO").replace("CRISTÓV?O", "CRISTÓVÃO").replace("YP?", "YPÊ")
    
    # Check exact or trimmed canonical match
    if name_clean in CANONICAL_TEAMS:
        return CANONICAL_TEAMS[name_clean]
    
    trimmed = name_clean.rstrip("… .").strip()
    if trimmed in CANONICAL_TEAMS:
        return CANONICAL_TEAMS[trimmed]

    for k, v in CANONICAL_TEAMS.items():
        if k.upper() == name_clean.upper() or k.upper() == trimmed.upper():
            return v

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


def is_team_match(clean: str, target: str) -> bool:
    """Robust matching for team names in report headers and sections."""
    if not clean or not target:
        return False
    c = clean.rstrip("… .").strip().upper()
    t = target.rstrip("… .").strip().upper()
    if c == t:
        return True
    if len(c) >= 6 and (c in t or t in c):
        return True
    return False


def parse_match_report_pdf(
    pdf_path: Path,
    match_id: int,
    competition: Optional[str] = None,
    category: Optional[str] = None,
    gender: Optional[str] = None,
) -> MatchData:
    """
    Parses a Match Report PDF into structured MatchData with validation.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Relatório PDF não encontrado em {pdf_path}")

    import fitz
    quick_doc = fitz.open(pdf_path)
    if not quick_doc.page_count:
        raise ValueError(f"PDF {pdf_path} não contém páginas")
    quick_text = quick_doc[0].get_text().strip()
    if not quick_text:
        raise ValueError(f"PDF {pdf_path} não possui texto extraível (vetorial/curvas)")

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError(f"PDF {pdf_path} não contém páginas")
        # Extract formatted layout text
        layout_text = pdf.pages[0].extract_text(layout=True)

    lines = layout_text.split("\n")

    # 1. Metadata & Teams
    meta_date, meta_time, meta_comp = extract_match_metadata(layout_text, match_id)
    raw_home, raw_away, home_team, away_team, home_sets, away_sets = extract_teams(lines)

    # Resolve metadata
    final_comp = competition or meta_comp or ("SUPERLIGA" if "SUPERLIGA" in layout_text.upper() else "CBS")
    final_gender = gender
    if not final_gender:
        if "FEMININ" in layout_text.upper():
            final_gender = "feminino"
        else:
            final_gender = "masculino"
    final_cat = category or ("A" if "SUPERLIGA" in final_comp.upper() else "sub18")

    # 2. Set Scores
    sets = extract_set_scores(lines, match_id)

    # 3. Locate Team Sections
    home_idx = None
    away_idx = None
    footer_idx = None

    for i, line in enumerate(lines):
        clean = line.strip()
        if (is_team_match(clean, raw_home) or is_team_match(clean, home_team)) and i > 5 and home_idx is None:
            home_idx = i
        elif (is_team_match(clean, raw_away) or is_team_match(clean, away_team)) and home_idx is not None and away_idx is None:
            away_idx = i
        elif any(k in line for k in ["BP Break point", "PONTOS GERAIS", "Pontos GERAIS", "Legenda:"]) and away_idx is not None:
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
        date=meta_date,
        time_str=meta_time,
        competition=final_comp,
        category=final_cat,
        gender=final_gender,
        home_team=home_team,
        away_team=away_team,
        home_sets=home_sets,
        away_sets=away_sets,
    )

    from cbv.parser.tactical import extract_tactical_data

    # 6. Extract Tactical Intelligence
    tactical_data = extract_tactical_data(
        pdf_path=pdf_path,
        match_id=match_id,
        home_team=home_team,
        away_team=away_team,
        home_lines=home_lines,
        away_lines=away_lines,
    )

    match_data = MatchData(
        match=match_model,
        sets=sets,
        players=all_players,
        teams=all_teams,
        tactical=tactical_data,
        parser_version=PARSER_VERSION,
    )

    # 7. Validation
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
