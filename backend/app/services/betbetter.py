import httpx
from cachetools import TTLCache
from typing import Optional

# BetBetter is free, no API key required
_betbetter_cache = TTLCache(maxsize=50, ttl=1800)

class BetBetterClient:
    """Free model picks API - no key needed."""
    BASE = "https://api.betbetter.world"  # Check their OpenAPI at /api/openapi.json
    
    async def get_picks(self, league: str = "soccer/epl") -> list:
        cache_key = f"picks_{league}"
        if cache_key in _betbetter_cache:
            return _betbetter_cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE}/picks/{league}")
            resp.raise_for_status()
            data = resp.json()
        
        _betbetter_cache[cache_key] = data
        return data
    
    async def get_predicted_scores(self, league: str = "soccer/epl") -> list:
        cache_key = f"scores_{league}"
        if cache_key in _betbetter_cache:
            return _betbetter_cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE}/predicted-scores/{league}")
            resp.raise_for_status()
            data = resp.json()
        
        _betbetter_cache[cache_key] = data
        return data