"""
Best-effort client activity logging for the admin Logs page.

Failures here must never break public endpoints (update check / device register).
"""
from __future__ import annotations

from typing import Any

from fastapi import Request

from app.database.supabase_client import get_supabase


def client_ip(request: Request) -> str | None:
    """Prefer the left-most X-Forwarded-For hop (Render / reverse proxies)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    if request.client and request.client.host:
        return request.client.host
    return None


def client_user_agent(request: Request) -> str | None:
    ua = request.headers.get("user-agent")
    if not ua:
        return None
    return ua[:500]


def log_request_event(
    *,
    event_type: str,
    request: Request | None = None,
    application_id: str | None = None,
    app_key: str | None = None,
    platform: str | None = None,
    app_version: str | None = None,
    build_number: int | None = None,
    result: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        supabase = get_supabase()
        resolved_app_id = application_id
        if resolved_app_id is None and app_key:
            app_res = (
                supabase.table("apps")
                .select("id")
                .eq("app_key", app_key)
                .limit(1)
                .execute()
            )
            if app_res.data:
                resolved_app_id = app_res.data[0]["id"]

        row = {
            "event_type": event_type,
            "application_id": resolved_app_id,
            "app_key": app_key,
            "platform": platform,
            "app_version": app_version,
            "build_number": build_number,
            "ip_address": ip_address if ip_address is not None else (client_ip(request) if request else None),
            "user_agent": user_agent if user_agent is not None else (client_user_agent(request) if request else None),
            "result": result,
            "metadata": metadata or {},
        }
        supabase.table("request_logs").insert(row).execute()
    except Exception:  # noqa: BLE001
        # Logging must never surface to clients.
        return
