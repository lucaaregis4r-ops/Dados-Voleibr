"""Team match statistics and aggregate match payload model."""

from typing import Optional, List
from pydantic import BaseModel, Field
from cbv.models.match import Match, SetScore
from cbv.models.player import PlayerMatchStats


class TeamMatchStats(BaseModel):
    """Aggregate statistics for a team in a match."""
    match_id: int
    team: str
    coach: Optional[str] = None
    assistant: Optional[str] = None

    # Points
    points_total: Optional[int] = None
    break_points: Optional[int] = None
    win_loss: Optional[int] = None

    # Serve
    serve_attempts: Optional[int] = None
    serve_errors: Optional[int] = None
    serve_points: Optional[int] = None

    # Reception
    reception_attempts: Optional[int] = None
    reception_errors: Optional[int] = None
    reception_positive_pct: Optional[float] = None
    reception_excellent_pct: Optional[float] = None

    # Attack
    attack_attempts: Optional[int] = None
    attack_errors: Optional[int] = None
    attack_blocked: Optional[int] = None
    attack_points: Optional[int] = None
    attack_points_pct: Optional[float] = None

    # Block
    block_points: Optional[int] = None

    # Opponent errors
    opponent_errors: Optional[int] = None


class MatchData(BaseModel):
    """Complete structured match data ready for database insertion."""
    match: Match
    sets: List[SetScore] = Field(default_factory=list)
    players: List[PlayerMatchStats] = Field(default_factory=list)
    teams: List[TeamMatchStats] = Field(default_factory=list)
    validation_status: str = "PENDING"
    validation_warnings: List[str] = Field(default_factory=list)
    parser_version: str = "0.1.0"
