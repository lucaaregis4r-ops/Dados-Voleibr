"""DuckDB database repository for storing and querying match data idempotently."""

from pathlib import Path
from typing import Optional, List, Dict, Any
import duckdb

from cbv.config import DUCKDB_PATH, logger
from cbv.models.stats import MatchData

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DatabaseRepository:
    """Manages DuckDB connections, schema migrations, and idempotent data operations."""

    def __init__(self, db_path: Path = DUCKDB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def init_db(self):
        """Initializes database tables from schema.sql."""
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            conn.execute(schema_sql)
        logger.debug(f"DuckDB initialized at {self.db_path}")

    def match_exists(self, match_id: int) -> bool:
        """Checks if a match_id is already stored in the database."""
        with self.get_connection() as conn:
            res = conn.execute("SELECT 1 FROM matches WHERE match_id = ?", [match_id]).fetchone()
            return res is not None

    def save_match_data(self, data: MatchData) -> None:
        """
        Stores MatchData idempotently within a transaction.
        Removes any previous rows for this match_id to guarantee no duplicate records.
        """
        match_id = data.match.match_id

        with self.get_connection() as conn:
            conn.begin()
            try:
                # 1. Clean existing records for this match
                conn.execute("DELETE FROM sets WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM player_match_stats WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM team_match_stats WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM matches WHERE match_id = ?", [match_id])

                # 2. Insert match
                m = data.match
                conn.execute(
                    """
                    INSERT INTO matches (
                        match_id, date, time_str, competition, category, gender,
                        home_team, away_team, home_sets, away_sets, validation_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        m.match_id,
                        m.date,
                        m.time_str,
                        m.competition,
                        m.category,
                        m.gender,
                        m.home_team,
                        m.away_team,
                        m.home_sets,
                        m.away_sets,
                        data.validation_status,
                    ],
                )

                # 3. Insert sets
                for s in data.sets:
                    conn.execute(
                        """
                        INSERT INTO sets (
                            match_id, set_number, home_points, away_points,
                            duration_minutes, partial_scores
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        [
                            s.match_id,
                            s.set_number,
                            s.home_points,
                            s.away_points,
                            s.duration_minutes,
                            s.partial_scores,
                        ],
                    )

                # 4. Insert players
                for p in data.players:
                    conn.execute(
                        """
                        INSERT INTO player_match_stats (
                            match_id, team, player_number, player_name, is_libero,
                            rating, points_total, break_points, win_loss,
                            serve_attempts, serve_errors, serve_points,
                            reception_attempts, reception_errors,
                            reception_positive_pct, reception_excellent_pct,
                            attack_attempts, attack_errors, attack_blocked,
                            attack_points, attack_points_pct, block_points
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            p.match_id,
                            p.team,
                            p.player_number,
                            p.player_name,
                            p.is_libero,
                            p.rating,
                            p.points_total,
                            p.break_points,
                            p.win_loss,
                            p.serve_attempts,
                            p.serve_errors,
                            p.serve_points,
                            p.reception_attempts,
                            p.reception_errors,
                            p.reception_positive_pct,
                            p.reception_excellent_pct,
                            p.attack_attempts,
                            p.attack_errors,
                            p.attack_blocked,
                            p.attack_points,
                            p.attack_points_pct,
                            p.block_points,
                        ],
                    )

                # 5. Insert team totals
                for t in data.teams:
                    conn.execute(
                        """
                        INSERT INTO team_match_stats (
                            match_id, team, coach, assistant, points_total,
                            break_points, win_loss, serve_attempts, serve_errors,
                            serve_points, reception_attempts, reception_errors,
                            reception_positive_pct, reception_excellent_pct,
                            attack_attempts, attack_errors, attack_blocked,
                            attack_points, attack_points_pct, block_points,
                            opponent_errors
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            t.match_id,
                            t.team,
                            t.coach,
                            t.assistant,
                            t.points_total,
                            t.break_points,
                            t.win_loss,
                            t.serve_attempts,
                            t.serve_errors,
                            t.serve_points,
                            t.reception_attempts,
                            t.reception_errors,
                            t.reception_positive_pct,
                            t.reception_excellent_pct,
                            t.attack_attempts,
                            t.attack_errors,
                            t.attack_blocked,
                            t.attack_points,
                            t.attack_points_pct,
                            t.block_points,
                            t.opponent_errors,
                        ],
                    )

                conn.commit()
                logger.info(f"game={match_id} saved to DuckDB ({len(data.players)} players)")
            except Exception as e:
                conn.rollback()
                logger.error(f"game={match_id} DuckDB transaction error: {e}")
                raise


# Default repository instance
default_repo = DatabaseRepository()
