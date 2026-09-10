"""In-app announcements — one-shot messages polled by Flutter apps (no Firebase)."""
from fastapi import HTTPException, status

from app.database.supabase_client import get_supabase
from app.schemas.announcement import (
    AnnouncementCheckRequest,
    AnnouncementCheckResponse,
    AnnouncementCreateRequest,
    AnnouncementOut,
)


def check_announcement(payload: AnnouncementCheckRequest) -> AnnouncementCheckResponse:
    """Return the newest published announcement for this app.

    The Flutter client shows each announcement id at most once (local dismiss).
    Publishing again requires creating a new announcement row.
    """
    supabase = get_supabase()
    app_res = (
        supabase.table("apps")
        .select("id, is_active")
        .eq("app_key", payload.app_key)
        .limit(1)
        .execute()
    )
    if not app_res.data or not app_res.data[0]["is_active"]:
        return AnnouncementCheckResponse(has_announcement=False)

    application_id = app_res.data[0]["id"]
    res = (
        supabase.table("in_app_announcements")
        .select("id, title, message, created_at")
        .eq("application_id", application_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return AnnouncementCheckResponse(has_announcement=False)

    row = res.data[0]
    return AnnouncementCheckResponse(
        has_announcement=True,
        announcement=AnnouncementOut(
            id=row["id"],
            title=row["title"],
            message=row["message"],
            created_at=row.get("created_at"),
        ),
    )


def create_announcement(payload: AnnouncementCreateRequest) -> dict:
    supabase = get_supabase()
    app_res = (
        supabase.table("apps")
        .select("id")
        .eq("id", str(payload.application_id))
        .limit(1)
        .execute()
    )
    if not app_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    row = {
        "application_id": str(payload.application_id),
        "title": payload.title,
        "message": payload.message,
    }
    res = supabase.table("in_app_announcements").insert(row).execute()
    return res.data[0]


def list_announcements(application_id: str | None = None) -> list:
    supabase = get_supabase()
    query = supabase.table("in_app_announcements").select("*")
    if application_id:
        query = query.eq("application_id", application_id)
    res = query.order("created_at", desc=True).limit(100).execute()
    return res.data or []
