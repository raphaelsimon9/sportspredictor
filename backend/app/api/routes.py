from fastapi import APIRouter, HTTPException
from typing import List
from app.services.football_data import FootballDataClient
from app.services.odds_api import OddsAPIClient
from app.services.betbetter import BetBetterClient
from app.services.predictor import PoissonPredictor, find_value_bets
from app.models.schemas import Match, Prediction, ValueBet

router = APIRouter(prefix="/api")

# Singleton model instance
_model = PoissonPredictor()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/model/train")
async def train_model(competition: str = "PL", season: int = 2024):
    """Train the Poisson model on historical data."""
    fd = FootballDataClient()
    matches = await fd.get_historical_matches(competition, season)
    if not matches:
        raise HTTPException(400, "No historical matches found")
    _model.fit(matches)
    return {"status": "trained", "matches_used": len(matches), 
            "teams_learned": len(_model.team_attack)}

@router.get("/matches", response_model=List[Match])
async def get_matches(competition: str = "PL", days: int = 7):
    """Get upcoming matches with odds."""
    fd = FootballDataClient()
    matches = await fd.get_matches(competition, date_to=None)
    
    # Enrich with odds if available (careful with quota!)
    try:
        odds_client = OddsAPIClient()
        sport_map = {"PL": "soccer_epl", "BL1": "soccer_germany_bundesliga", 
                     "SA": "soccer_italy_serie_a", "PD": "soccer_spain_la_liga",
                     "FL1": "soccer_france_ligue_one"}
        sport = sport_map.get(competition)
        if sport:
            events = await odds_client.get_odds(sport)
            event_map = {e["home_team"].lower(): e for e in events}
            for m in matches:
                ev = event_map.get(m.home_team.lower())
                if ev:
                    m.odds = odds_client.parse_match_odds(ev)
    except Exception:
        pass  # Odds unavailable — still return fixtures
    
    return matches[:50]

@router.get("/predictions", response_model=List[Prediction])
async def get_predictions(competition: str = "PL"):
    """Get model predictions for upcoming matches."""
    if not _model.is_fitted:
        # Auto-train if not fitted
        await train_model(competition)
    
    fd = FootballDataClient()
    matches = await fd.get_matches(competition)
    preds = []
    for m in matches:
        try:
            preds.append(_model.predict(m.home_team, m.away_team, m.id))
        except Exception:
            continue
    return preds

@router.get("/value-bets", response_model=List[ValueBet])
async def get_value_bets(competition: str = "PL", min_ev: float = 0.05):
    """Find value bets: where model probability > implied probability."""
    if not _model.is_fitted:
        await train_model(competition)
    
    fd = FootballDataClient()
    matches = await fd.get_matches(competition)
    
    # Get odds
    odds_client = OddsAPIClient()
    sport_map = {"PL": "soccer_epl", "BL1": "soccer_germany_bundesliga",
                 "SA": "soccer_italy_serie_a", "PD": "soccer_spain_la_liga",
                 "FL1": "soccer_france_ligue_one"}
    sport = sport_map.get(competition)
    
    if sport:
        try:
            events = await odds_client.get_odds(sport)
            event_map = {e["home_team"].lower(): e for e in events}
            for m in matches:
                ev = event_map.get(m.home_team.lower())
                if ev:
                    m.odds = odds_client.parse_match_odds(ev)
        except Exception:
            pass
    
    preds = [_model.predict(m.home_team, m.away_team, m.id) for m in matches]
    bets = find_value_bets(preds, matches, min_ev)
    return bets

@router.get("/betbetter/picks")
async def get_betbetter_picks(league: str = "soccer/epl"):
    """Supplement with free BetBetter model picks (no API key needed)."""
    client = BetBetterClient()
    try:
        picks = await client.get_picks(league)
        return picks[:20]
    except Exception as e:
        return {"error": str(e), "note": "BetBetter may be down or league unavailable"}