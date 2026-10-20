"""Tactical data models for volleyball match analysis."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PhaseAttackStats(BaseModel):
    """Attack statistics for a specific tactical phase (K1 Positive, K1 Negative, K2 Transition)."""
    phase_name: str
    attempts: int = 0
    points: int = 0
    points_pct: float = 0.0
    blocked: int = 0
    errors: int = 0
    efficiency_pct: Optional[float] = None


class SideOutBreakPointStats(BaseModel):
    """Side-Out and Break Point phase efficiency."""
    team: str
    receptions_total: int = 0
    sideout_points: int = 0
    sideout_rate: Optional[float] = None  # Receptions per SO point
    serves_total: int = 0
    breakpoint_points: int = 0
    breakpoint_rate: Optional[float] = None  # Serves per BP point


class SetTacticalStats(BaseModel):
    """Skills and scoring breakdown for a specific set."""
    match_id: int
    team: str
    set_number: int
    # Points source
    serve_points_won: int = 0
    attack_points_won: int = 0
    block_points_won: int = 0
    opponent_errors_won: int = 0
    # Serve skill
    serve_total: int = 0
    serve_errors: int = 0
    serve_aces: int = 0
    # Reception skill
    reception_total: int = 0
    reception_errors: int = 0
    reception_positive_pct: Optional[float] = None
    reception_excellent_pct: Optional[float] = None
    # Attack skill
    attack_total: int = 0
    attack_errors: int = 0
    attack_blocked: int = 0
    attack_points: int = 0
    attack_points_pct: Optional[float] = None


class TeamTacticalStats(BaseModel):
    """Complete tactical metrics for a single team in a match."""
    match_id: int
    team: str
    sideout: SideOutBreakPointStats
    rotations: Dict[str, int] = Field(default_factory=dict)  # {'p1': diff, ..., 'p6': diff}
    positive_reception_attack: PhaseAttackStats
    negative_reception_attack: PhaseAttackStats
    transition_attack: PhaseAttackStats
    set_breakdowns: List[SetTacticalStats] = Field(default_factory=list)


class MatchTacticalData(BaseModel):
    """Aggregated tactical report for both teams in a match."""
    match_id: int
    home_team: str
    away_team: str
    home_tactics: TeamTacticalStats
    away_tactics: TeamTacticalStats
