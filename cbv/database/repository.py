"""DuckDB database repository for storing and querying match data idempotently."""

from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import duckdb
from cbv.config import DUCKDB_PATH, logger
from cbv.models.stats import MatchData

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DatabaseRepository:
    """Manages DuckDB connections, schema migrations, and idempotent data operations."""

    def __init__(self, db_path: Path = DUCKDB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self.db_path))
        self.init_db()

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        return self._conn.cursor()

    def init_db(self):
        """Initializes database tables from schema.sql."""
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        with self._lock:
            cur = self.get_connection()
            cur.execute(schema_sql)
            from cbv.metric_definitions import METRICS, VERSION
            for key, name, columns, denominator, cls, formula in METRICS:
                cur.execute("INSERT OR REPLACE INTO metric_definitions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            [key, name, name, formula, cls, 'match report agregado', 20, VERSION])
        logger.debug(f"DuckDB initialized at {self.db_path}")

    def match_exists(self, match_id: int) -> bool:
        """Checks if a match_id is already stored in the database."""
        with self._lock:
            cur = self.get_connection()
            res = cur.execute("SELECT 1 FROM matches WHERE match_id = ?", [match_id]).fetchone()
            return res is not None

    def save_match_data(self, data: MatchData) -> None:
        """
        Stores MatchData idempotently within a transaction.
        Removes any previous rows for this match_id to guarantee no duplicate records.
        """
        match_id = data.match.match_id

        with self._lock:
            conn = self.get_connection()
            conn.execute("CREATE TABLE IF NOT EXISTS match_ingest_attempts(match_id BIGINT PRIMARY KEY,status VARCHAR,attempted_at TIMESTAMP,payload JSON)")
            previous=conn.execute("SELECT validation_status FROM matches WHERE match_id=?",[match_id]).fetchone()
            if previous and previous[0]=='VALID' and data.validation_status!='VALID':
                conn.execute("INSERT OR REPLACE INTO match_ingest_attempts VALUES (?,?,current_timestamp,?)",[match_id,data.validation_status,data.model_dump_json()])
                logger.warning(f"game={match_id} refresh rejected ({data.validation_status}); retaining last valid Match Report")
                return
            conn.begin()
            try:
                # 1. Clean existing records for this match
                conn.execute("DELETE FROM sets WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM player_match_stats WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM team_match_stats WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM team_tactical_stats WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM set_tactical_stats WHERE match_id = ?", [match_id])
                conn.execute("DELETE FROM matches WHERE match_id = ?", [match_id])


                # 2. Insert match
                m = data.match
                from cbv.seasons import default_match_season
                season_val = m.season or default_match_season(m.competition,m.date)

                conn.execute(
                    """
                    INSERT INTO matches (
                        match_id, date, time_str, competition, category, gender, season,
                        home_team, away_team, home_sets, away_sets, validation_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        m.match_id,
                        m.date,
                        m.time_str,
                        m.competition,
                        m.category,
                        m.gender,
                        season_val,
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

                # 6. Insert tactical intelligence if available
                if data.tactical:
                    for team_tac in [data.tactical.home_tactics, data.tactical.away_tactics]:
                        so = team_tac.sideout
                        rot = team_tac.rotations
                        k1_pos = team_tac.positive_reception_attack
                        k1_neg = team_tac.negative_reception_attack
                        k2 = team_tac.transition_attack

                        conn.execute(
                            """
                            INSERT INTO team_tactical_stats (
                                match_id, team, sideout_points, sideout_receptions, sideout_rate,
                                breakpoint_points, breakpoint_serves, breakpoint_rate,
                                p1_diff, p2_diff, p3_diff, p4_diff, p5_diff, p6_diff,
                                pos_rec_att_attempts, pos_rec_att_points, pos_rec_att_points_pct,
                                pos_rec_att_blocked, pos_rec_att_errors, pos_rec_att_efficiency_pct,
                                neg_rec_att_attempts, neg_rec_att_points, neg_rec_att_points_pct,
                                neg_rec_att_blocked, neg_rec_att_errors, neg_rec_att_efficiency_pct,
                                trans_att_attempts, trans_att_points, trans_att_points_pct,
                                trans_att_blocked, trans_att_errors, trans_att_efficiency_pct
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            [
                                match_id,
                                team_tac.team,
                                so.sideout_points,
                                so.receptions_total,
                                so.sideout_rate,
                                so.breakpoint_points,
                                so.serves_total,
                                so.breakpoint_rate,
                                rot.get("p1", 0),
                                rot.get("p2", 0),
                                rot.get("p3", 0),
                                rot.get("p4", 0),
                                rot.get("p5", 0),
                                rot.get("p6", 0),
                                k1_pos.attempts,
                                k1_pos.points,
                                k1_pos.points_pct,
                                k1_pos.blocked,
                                k1_pos.errors,
                                k1_pos.efficiency_pct,
                                k1_neg.attempts,
                                k1_neg.points,
                                k1_neg.points_pct,
                                k1_neg.blocked,
                                k1_neg.errors,
                                k1_neg.efficiency_pct,
                                k2.attempts,
                                k2.points,
                                k2.points_pct,
                                k2.blocked,
                                k2.errors,
                                k2.efficiency_pct,
                            ],
                        )

                        # Set tactical breakdowns
                        for set_tac in team_tac.set_breakdowns:
                            conn.execute(
                                """
                                INSERT INTO set_tactical_stats (
                                    match_id, team, set_number,
                                    serve_points_won, attack_points_won, block_points_won, opponent_errors_won,
                                    serve_total, serve_errors, serve_aces,
                                    reception_total, reception_errors, reception_positive_pct, reception_excellent_pct,
                                    attack_total, attack_errors, attack_blocked, attack_points, attack_points_pct
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                [
                                    match_id,
                                    set_tac.team,
                                    set_tac.set_number,
                                    set_tac.serve_points_won,
                                    set_tac.attack_points_won,
                                    set_tac.block_points_won,
                                    set_tac.opponent_errors_won,
                                    set_tac.serve_total,
                                    set_tac.serve_errors,
                                    set_tac.serve_aces,
                                    set_tac.reception_total,
                                    set_tac.reception_errors,
                                    set_tac.reception_positive_pct,
                                    set_tac.reception_excellent_pct,
                                    set_tac.attack_total,
                                    set_tac.attack_errors,
                                    set_tac.attack_blocked,
                                    set_tac.attack_points,
                                    set_tac.attack_points_pct,
                                ],
                            )

                conn.execute("INSERT OR REPLACE INTO match_provenance VALUES (?, ?, ?, NULL, ?, ?)",
                             [match_id, f"https://cbv.com.br/jogo/{match_id}", None, 'cbv-parser-0.1.0', 'scouting-1.0'])
                conn.commit()
                # In-process dossiers and role estimates must not survive an ingestion.
                from cbv.analysis.tactics import get_team_tactical_dossier
                from cbv.analysis.setter_distribution import infer_team_tactical_roles
                get_team_tactical_dossier.cache_clear()
                infer_team_tactical_roles.cache_clear()
                logger.info(f"game={match_id} saved to DuckDB ({len(data.players)} players, tactical={'yes' if data.tactical else 'no'})")
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.error(f"game={match_id} DuckDB transaction error: {e}")
                raise


# Default repository instance
default_repo = DatabaseRepository()
