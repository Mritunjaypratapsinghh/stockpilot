from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


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

    # CORS
    cors_origins: Optional[str] = None  # Comma-separated list of allowed origins

    # Google OAuth
    google_client_id: str = ""

    class Config:
        env_file = "../.env"  # Relative to backend/ directory where uvicorn is run


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
