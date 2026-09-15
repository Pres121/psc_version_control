from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.auth.dependencies import get_current_admin
from app.core.config import get_settings
from app.core.limiter import limiter
from app.database.supabase_client import get_supabase
from app.schemas.notification import (
    DeviceRegisterRequest,
    NotificationLogOut,
    NotificationSendRequest,
)
from app.services.log_service import log_request_event
from app.services.notification_service import send_release_notification, subscribe_token_to_topic

router = APIRouter(prefix="/notifications", tags=["notifications"])
settings = get_settings()


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
@limiter.limit(settings.DEVICE_REGISTER_RATE_LIMIT)
def register_device(request: Request, payload: DeviceRegisterRequest):
    """Called by Flutter apps at startup to subscribe a device's FCM token
    to its app's topic. Public endpoint - no admin data is exposed here."""
    supabase = get_supabase()
    app_res = (
        supabase.table("apps")
        .select("id, app_key")
        .eq("app_key", payload.app_key)
        .limit(1)
        .execute()
    )
    if not app_res.data:
        log_request_event(
            event_type="device_register",
            request=request,
            app_key=payload.app_key,
            platform=payload.platform,
            app_version=payload.app_version,
            result="unknown_app_key",
        )
        return {"registered": False, "reason": "unknown app_key"}

    application_id = app_res.data[0]["id"]
    topic = app_res.data[0]["app_key"]
    now = datetime.now(timezone.utc).isoformat()

    supabase.table("devices").upsert(
        {
            "application_id": application_id,
            "platform": payload.platform,
            "fcm_token": payload.fcm_token,
            "app_version": payload.app_version,
            "last_seen_at": now,
        },
        on_conflict="fcm_token",
    ).execute()

    # Server-side topic subscribe so topic broadcasts actually reach the device.
    topic_subscribed = False
    subscribe_error: str | None = None
    try:
        subscribe_token_to_topic(payload.fcm_token, topic)
        topic_subscribed = True
    except Exception as exc:  # noqa: BLE001
        subscribe_error = str(getattr(exc, "detail", None) or exc)

    log_request_event(
        event_type="device_register",
        request=request,
        application_id=application_id,
        app_key=payload.app_key,
        platform=payload.platform,
        app_version=payload.app_version,
        result="registered" if topic_subscribed else "registered_topic_pending",
        metadata={"fcm_topic": topic, "topic_subscribed": topic_subscribed, "subscribe_error": subscribe_error},
    )
    return {
        "registered": True,
        "topic": topic,
        "topic_subscribed": topic_subscribed,
    }
