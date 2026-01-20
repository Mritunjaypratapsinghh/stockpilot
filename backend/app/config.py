from pydantic_settings import BaseSettings
from functools import lru_cache

# External API URLs (public, not secrets)
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com"
YAHOO_CHART_URL = f"{YAHOO_FINANCE_BASE}/v8/finance/chart"
YAHOO_SEARCH_URL = f"{YAHOO_FINANCE_BASE}/v1/finance/search"
YAHOO_QUOTE_URL = f"{YAHOO_FINANCE_BASE}/v10/finance/quoteSummary"

class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    mongodb_db: str = "stockpilot"
    
    # JWT
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # Telegram
    telegram_bot_token: str = ""
    
    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
