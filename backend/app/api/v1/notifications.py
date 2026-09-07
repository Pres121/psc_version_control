from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_admin
from app.database.supabase_client import get_supabase
from app.schemas.notification import (
    DeviceRegisterRequest,
    NotificationLogOut,
    NotificationSendRequest,
)
from app.services.notification_service import send_release_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send", response_model=dict)
def send_notification(payload: NotificationSendRequest, admin: dict = Depends(get_current_admin)):
    return send_release_notification(
        application_id=str(payload.application_id),
        release_id=str(payload.release_id),
        title=payload.title,
        message=payload.message,
    )


@router.get("/history", response_model=list[NotificationLogOut])
def notification_history(
    application_id: UUID | None = None, admin: dict = Depends(get_current_admin)
):
    supabase = get_supabase()
    query = supabase.table("notification_logs").select("*")
    if application_id:
        query = query.eq("application_id", str(application_id))
    res = query.order("created_at", desc=True).execute()
    return res.data


@router.post("/devices/register", status_code=201)
def register_device(payload: DeviceRegisterRequest):
    """Called by Flutter apps at startup to subscribe a device's FCM token
    to its app's topic. Public endpoint - no admin data is exposed here."""
    supabase = get_supabase()
    app_res = supabase.table("apps").select("id").eq("app_key", payload.app_key).limit(1).execute()
    if not app_res.data:
        return {"registered": False, "reason": "unknown app_key"}

    application_id = app_res.data[0]["id"]
    supabase.table("devices").upsert(
        {
            "application_id": application_id,
            "platform": payload.platform,
            "fcm_token": payload.fcm_token,
            "app_version": payload.app_version,
        },
        on_conflict="fcm_token",
    ).execute()
    return {"registered": True}
