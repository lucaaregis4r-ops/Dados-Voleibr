import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SetScore(BaseModel):
    """Score and duration details for an individual set."""
    match_id: int
    set_number: int
    home_points: int
    away_points: int
    duration_minutes: Optional[int] = None
    partial_scores: Optional[str] = None


class Match(BaseModel):
    """Match metadata and overall result."""
    match_id: int
    date: Optional[datetime.date] = None

    time_str: Optional[str] = None
    competition: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    season: Optional[str] = None
    home_team: str
    away_team: str
    home_sets: Optional[int] = None
    away_sets: Optional[int] = None
    hall: Optional[str] = None
    city: Optional[str] = None
    spectators: Optional[int] = None
    validation_status: str = Field(default="PENDING")
