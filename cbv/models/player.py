"""Player match statistics model."""

from typing import Optional, List
from pydantic import BaseModel, Field


class PlayerMatchStats(BaseModel):
    """Statistics for an individual player in a specific match."""
    match_id: int
    team: str
    player_number: int
    player_name: str
    is_libero: bool = False
    starting_positions: List[Optional[str]] = Field(default_factory=list)
    rating: Optional[float] = None

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
