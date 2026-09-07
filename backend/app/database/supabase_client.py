"""
Thin wrapper around the Supabase client.

Uses the service_role key on the server only. This key must never be
sent to Flutter apps or the admin dashboard frontend - all privileged
DB access happens behind the FastAPI layer.
"""
from functools import lru_cache

from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
