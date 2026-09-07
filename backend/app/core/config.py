"""
Centralized application configuration.
All values are loaded from environment variables (see .env.example).
Never hard-code secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "PSC Update Management API"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DOCS_ENABLED: bool = True

    # --- Supabase / Postgres ---
    SUPABASE_URL: str
    SUPABASE_KEY: str  # service_role key - server-side only, never sent to clients
    DATABASE_URL: str | None = None

    # --- Auth ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # --- CORS ---
    ALLOWED_ORIGINS: List[str] = ["*"]

    # --- FCM ---
    FCM_PROJECT_ID: str | None = None
    FCM_CREDENTIALS_JSON: str | None = None  # path to service-account json, or raw JSON

    # --- Rate limiting ---
    UPDATE_CHECK_RATE_LIMIT: str = "60/minute"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
