import httpx
from cachetools import TTLCache
from datetime import datetime, timedelta
from typing import List, Optional
from app.config import settings
from app.models.schemas import Match

# Cache fixtures aggressively - football-data.org allows 10 req/min
_fixture_cache = TTLCache(maxsize=100, ttl=settings.CACHE_TTL_FIXTURES)

class FootballDataClient:
    BASE = "https://api.football-data.org/v4"
    
    def __init__(self):
        self.headers = {"X-Auth-Token": settings.FOOTBALL_DATA_API_KEY}
    
    async def get_matches(self, competition: str = "PL", 
                          date_from: Optional[str] = None,
                          date_to: Optional[str] = None) -> List[Match]:
        cache_key = f"matches_{competition}_{date_from}_{date_to}"
        if cache_key in _fixture_cache:
            return _fixture_cache[cache_key]
        
        if not date_from:
            date_from = datetime.now().strftime("%Y-%m-%d")
        if not date_to:
            date_to = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE}/competitions/{competition}/matches",
                headers=self.headers,
                params={"dateFrom": date_from, "dateTo": date_to, "status": "SCHEDULED"}
            )
            resp.raise_for_status()
            data = resp.json()
        
        matches = []
        for m in data.get("matches", []):
            matches.append(Match(
                id=str(m["id"]),
                competition=m["competition"]["name"],
                home_team=m["homeTeam"]["name"],
                away_team=m["awayTeam"]["name"],
                kickoff=datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
                status=m["status"],
            ))
        
        _fixture_cache[cache_key] = matches
        return matches
    
    async def get_historical_matches(self, competition: str = "PL", 
                                     season: int = 2024) -> List[Match]:
        """Fetch completed matches for model training."""
        cache_key = f"hist_{competition}_{season}"
        if cache_key in _fixture_cache:
            return _fixture_cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE}/competitions/{competition}/matches",
                headers=self.headers,
                params={"season": season, "status": "FINISHED"}
            )
            resp.raise_for_status()
            data = resp.json()
        
        matches = []
        for m in data.get("matches", []):
            matches.append(Match(
                id=str(m["id"]),
                competition=m["competition"]["name"],
                home_team=m["homeTeam"]["name"],
                away_team=m["awayTeam"]["name"],
                kickoff=datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
                status=m["status"],
                home_score=m["score"]["fullTime"]["home"],
                away_score=m["score"]["fullTime"]["away"],
            ))
        
        _fixture_cache[cache_key] = matches
        return matches