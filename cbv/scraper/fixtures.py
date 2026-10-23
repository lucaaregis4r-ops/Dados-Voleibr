"""Upcoming public fixtures scraper for CBV Superliga."""

import urllib.request
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from cbv.config import logger
from cbv.parser.match_report import normalize_team_name, CANONICAL_TEAMS
from cbv.database.repository import default_repo
from cbv.analysis.predictions import predict_matchup


FIXTURE_URLS = [
    {
        "url": "https://cbv.com.br/volei-de-quadra/superliga-a-masculina",
        "competition": "SUPERLIGA",
        "category": "A",
        "gender": "masculino",
    },
    {
        "url": "https://cbv.com.br/volei-de-quadra/superliga-a-feminina",
        "competition": "SUPERLIGA",
        "category": "A",
        "gender": "feminino",
    },
]


def extract_schedule_from_html(html: str) -> List[Dict[str, Any]]:
    """Extracts matchesByRound list from Next.js payload within the HTML."""
    pos = html.find("matchesByRound")
    if pos == -1:
        return []

    sub_start = html.rfind("{", 0, pos)
    depth = 0
    end_pos = sub_start
    for i in range(sub_start, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break

    raw = html[sub_start:end_pos].replace(r'\"', '"')
    try:
        obj = json.loads(raw)
        data = obj.get("matchesByRound", {})
    except Exception as e:
        logger.error(f"Error parsing matchesByRound JSON: {e}")
        return []

    fixtures = []
    for round_name, match_list in data.items():
        for m in match_list:
            fixtures.append({
                "match_id": m.get("ChampionshipMatch_ID"),
                "round_name": round_name,
                "datetime_raw": m.get("MatchDateTime"),
                "home_team_raw": m.get("HomeTeam"),
                "away_team_raw": m.get("GuestTeam"),
                "won_set_home": m.get("WonSetHome") or 0,
                "won_set_guest": m.get("WonSetGuest") or 0,
                "gym": m.get("court_number") or "",
            })
    return fixtures


def scrape_upcoming_fixtures() -> List[Dict[str, Any]]:
    """
    Scrapes the public upcoming Superliga schedule and stores source metadata.
    Forecasts are computed separately, only when the cohort has a fitted model.
    """
    all_upcoming = []

    for cfg in FIXTURE_URLS:
        url = cfg["url"]
        comp = cfg["competition"]
        cat = cfg["category"]
        gen = cfg["gender"]


        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Failed to fetch schedule from {url}: {e}")
            continue

        from cbv.seasons import source_season,register_edition,assign_source_matches
        from cbv.storage.raw import atomic_write,digest
        from cbv.config import RAW_DIR
        season=source_season(html)
        archive=RAW_DIR/'competitions'/season/gen
        atomic_write(archive/(digest(html.encode())+'.html'),html.encode())
        with default_repo.get_connection() as conn:register_edition(conn,comp,cat,gen,season,url,digest(html.encode()))
        fixtures = extract_schedule_from_html(html)
        with default_repo.get_connection() as conn:
            conn.begin()
            try:
                assign_source_matches(conn,[f['match_id'] for f in fixtures if f.get('match_id')],dict(competition=comp,category=cat,gender=gen,season=season),url,digest(html.encode()))
                conn.commit()
            except Exception:conn.rollback();raise
        logger.info(f"Extracted {len(fixtures)} total matches from schedule for {comp} {gen}")

        for f in fixtures:
            # Check if match is upcoming (not yet played)
            home_sets = f.get("won_set_home") or 0
            away_sets = f.get("won_set_guest") or 0
            is_played = (home_sets > 0 or away_sets > 0)

            home_norm = normalize_team_name(f["home_team_raw"] or "")
            away_norm = normalize_team_name(f["away_team_raw"] or "")

            if not home_norm or not away_norm:
                continue

            dt_raw = f.get("datetime_raw") or ""
            match_date = dt_raw.split("T")[0] if "T" in dt_raw else dt_raw
            match_time = dt_raw.split("T")[1][:5] if "T" in dt_raw else ""

            # Forecasts belong to Confronto → Modelo and require a fitted cohort.
            # Missing forecasts must stay missing rather than becoming synthetic 50/50s.
            pred_winner = None
            prob_home = None
            prob_away = None
            proj_score = None
            confidence = None

            record = {
                "match_id": f["match_id"],
                "competition": comp,
                "category": cat,
                "gender": gen,
                "season": season,
                "round_name": f["round_name"],
                "match_date": match_date,
                "match_time": match_time,
                "home_team": home_norm,
                "away_team": away_norm,
                "gym": f.get("gym") or "",
                "is_played": is_played,
                "predicted_winner": pred_winner,
                "predicted_prob_home": prob_home,
                "predicted_prob_away": prob_away,
                "projected_score": proj_score,
                "confidence": confidence,
            }

            all_upcoming.append(record)

    # Store into DuckDB
    with default_repo.get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS upcoming_matches (match_id BIGINT PRIMARY KEY, competition VARCHAR, category VARCHAR, gender VARCHAR, season VARCHAR, round_name VARCHAR, match_date VARCHAR, match_time VARCHAR, home_team VARCHAR, away_team VARCHAR, gym VARCHAR, predicted_winner VARCHAR, predicted_prob_home DOUBLE, predicted_prob_away DOUBLE, projected_score VARCHAR, confidence VARCHAR, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        
        for r in all_upcoming:
            conn.execute("DELETE FROM upcoming_matches WHERE match_id = ?", [r["match_id"]])
            conn.execute("""
                INSERT INTO upcoming_matches (
                    match_id, competition, category, gender, season, round_name,
                    match_date, match_time, home_team, away_team, gym,
                    predicted_winner, predicted_prob_home, predicted_prob_away,
                    projected_score, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                r["match_id"], r["competition"], r["category"], r["gender"], r["season"],
                r["round_name"], r["match_date"], r["match_time"], r["home_team"], r["away_team"],
                r["gym"], r["predicted_winner"], r["predicted_prob_home"], r["predicted_prob_away"],
                r["projected_score"], r["confidence"]
            ])

    logger.info(f"Successfully saved {len(all_upcoming)} fixtures into DuckDB upcoming_matches.")
    return all_upcoming


def get_stored_upcoming_fixtures(competition: Optional[str] = None, only_future: bool = True) -> List[Dict[str, Any]]:
    """Retrieves upcoming matches with predictions from DuckDB."""
    with default_repo.get_connection() as conn:
        query = """
            SELECT 
                match_id, competition, category, gender, season, round_name,
                match_date, match_time, home_team, away_team, gym,
                predicted_winner, predicted_prob_home, predicted_prob_away,
                projected_score, confidence
            FROM upcoming_matches
        """
        params = []
        if competition and competition != "ALL":
            query += " WHERE UPPER(competition || '_' || COALESCE(gender, '')) = UPPER(?) OR UPPER(competition) = UPPER(?)"
            params = [competition, competition]

        query += " ORDER BY match_date, match_time, match_id"
        df = conn.execute(query, params).fetchdf()

    return df.to_dict(orient="records")
