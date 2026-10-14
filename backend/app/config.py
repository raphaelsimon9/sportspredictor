from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FOOTBALL_DATA_API_KEY: str = ""
    ODDS_API_IO_KEY: str = ""
    THE_ODDS_API_KEY: str = ""
    FOOTBALL_CHARTS_KEY: str = ""
    
    # Cache TTLs (seconds)
    CACHE_TTL_FIXTURES: int = 3600      # 1 hour
    CACHE_TTL_ODDS: int = 21600         # 6 hours (preserve quota)
    CACHE_TTL_PREDICTIONS: int = 7200   # 2 hours
    
    class Config:
        env_file = ".env"

settings = Settings()