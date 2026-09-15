"""
Centralized application configuration.
All values are loaded from environment variables (see .env.example).
Never hard-code secrets here.
"""
import json
from functools import lru_cache
from typing import List, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_DEFAULT = "default-insecure-secret-key-change-in-production"


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "PSC Update Management API"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DOCS_ENABLED: bool = True

    # --- Supabase / Postgres ---
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # service_role key - server-side only, never sent to clients
    DATABASE_URL: str | None = None

    # --- Auth ---
    SECRET_KEY: str = _INSECURE_SECRET_DEFAULT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # --- CORS ---
    # Typed as Union[str, List[str]] so pydantic_settings doesn't fail json.loads() in EnvSettingsSource
    ALLOWED_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- FCM ---
    FCM_PROJECT_ID: str | None = None
    FCM_CREDENTIALS_JSON: str | None = None  # path to service-account json, or raw JSON

    # --- Rate limiting ---
    UPDATE_CHECK_RATE_LIMIT: str = "60/minute"
    LOGIN_RATE_LIMIT: str = "10/minute"
    DOWNLOAD_RATE_LIMIT: str = "30/minute"
    DEVICE_REGISTER_RATE_LIMIT: str = "30/minute"

    # --- App binary storage (Supabase Storage) ---
    STORAGE_BUCKET: str = "app-builds"
    # Public URL of this API (used to build download-page links for Flutter Update Now)
    PUBLIC_BASE_URL: str = "https://psc-version-control.onrender.com"
    SIGNED_URL_EXPIRE_SECONDS: int = 60 * 30  # 30 minutes

    # --- Email / OTP (Resend) ---
    RESEND_API_KEY: str | None = None
    RESEND_FROM_EMAIL: str = "PSC Update Hub <onboarding@resend.dev>"
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 5

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env = (self.ENVIRONMENT or "").lower()
        is_prod = env in {"production", "prod", "staging"}

        if is_prod:
            if not self.SECRET_KEY or self.SECRET_KEY == _INSECURE_SECRET_DEFAULT or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be a strong random string (32+ chars) when ENVIRONMENT is production/staging"
                )
            if not self.SUPABASE_URL or not self.SUPABASE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY are required in production/staging")
            if not self.RESEND_API_KEY:
                raise ValueError("RESEND_API_KEY is required in production/staging for OTP login emails")
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError(
                    "ALLOWED_ORIGINS must not include '*' in production/staging. "
                    "Set explicit admin dashboard origin(s)."
                )
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
