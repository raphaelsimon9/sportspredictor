from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Team(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    crest: Optional[str] = None

class MatchOdds(BaseModel):
    bookmaker: str
    home_win: float
    draw: float
    away_win: float
    updated_at: Optional[datetime] = None

class Match(BaseModel):
    id: str
    competition: str
    home_team: str
    away_team: str
    kickoff: datetime
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    odds: Optional[List[MatchOdds]] = None

class Prediction(BaseModel):
    match_id: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_home_goals: float
    predicted_away_goals: float
    model: str
    confidence: str  # HIGH / MEDIUM / LOW

class ValueBet(BaseModel):
    match_id: str
    match_label: str
    selection: str  # "HOME" / "DRAW" / "AWAY"
    bookmaker: str
    bookmaker_odds: float
    model_probability: float
    implied_probability: float
    expected_value: float  # as decimal, e.g. 0.15 = +15%
    confidence: str