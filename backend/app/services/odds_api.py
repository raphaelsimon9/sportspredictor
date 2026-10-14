import httpx
from cachetools import TTLCache
from typing import List, Optional
from app.config import settings
from app.models.schemas import MatchOdds

_odds_cache = TTLCache(maxsize=50, ttl=settings.CACHE_TTL_ODDS)

class OddsAPIClient:
    """The Odds API - 500 free requests/month. Cache aggressively."""
    BASE = "https://api.the-odds-api.com/v4"
    
    def __init__(self):
        self.api_key = settings.THE_ODDS_API_KEY
    
    async def get_odds(self, sport: str = "soccer_epl", 
                       regions: str = "uk,eu",
                       markets: str = "h2h") -> List[dict]:
        cache_key = f"odds_{sport}_{regions}_{markets}"
        if cache_key in _odds_cache:
            return _odds_cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE}/sports/{sport}/odds",
                params={
                    "apiKey": self.api_key,
                    "regions": regions,
                    "markets": markets,
                    "oddsFormat": "decimal"
                }
            )
            resp.raise_for_status()
            data = resp.json()
        
        _odds_cache[cache_key] = data
        return data
    
    def parse_match_odds(self, event: dict) -> List[MatchOdds]:
        """Extract h2h odds from The Odds API event format."""
        odds_list = []
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] != "h2h":
                    continue
                outcomes = {o["name"]: o["price"] for o in market["outcomes"]}
                home = event["home_team"]
                away = event["away_team"]
                odds_list.append(MatchOdds(
                    bookmaker=bookmaker["title"],
                    home_win=outcomes.get(home, 0),
                    draw=outcomes.get("Draw", 0),
                    away_win=outcomes.get(away, 0),
                ))
        return odds_list