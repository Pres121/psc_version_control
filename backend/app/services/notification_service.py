"""
Firebase Cloud Messaging integration.

Notifications are targeted per-application using FCM topics named after
each app's app_key (e.g. "psc_notes"), so a PSC Notes release never
reaches PSC Calendar users. Each Flutter app subscribes only to its own
app_key topic on startup.
"""
import json
from datetime import datetime, timezone

import firebase_admin
from fastapi import HTTPException, status
from firebase_admin import credentials, messaging

from app.core.config import get_settings
from app.database.supabase_client import get_supabase

_firebase_app: firebase_admin.App | None = None


def _get_firebase_app() -> firebase_admin.App:
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    settings = get_settings()
    if not settings.FCM_CREDENTIALS_JSON:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FCM is not configured on this server",
        )

    raw = settings.FCM_CREDENTIALS_JSON
    try:
        # allow either a raw JSON string or a path to a service-account file
        cred_info = json.loads(raw) if raw.strip().startswith("{") else None
        cred = credentials.Certificate(cred_info) if cred_info else credentials.Certificate(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid FCM credentials: {exc}",
        ) from exc

    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_release_notification(application_id: str, release_id: str, title: str, message: str) -> dict:
    supabase = get_supabase()

    # Prevent accidental duplicate notifications for the same release.
    existing = (
        supabase.table("notification_logs")
        .select("id")
        .eq("release_id", release_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A notification has already been sent for this release",
        )

    app_res = supabase.table("apps").select("app_key").eq("id", application_id).limit(1).execute()
    if not app_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    topic = app_res.data[0]["app_key"]

    log_row = {
        "application_id": application_id,
        "release_id": release_id,
        "title": title,
        "message": message,
        "fcm_topic": topic,
        "status": "pending",
    }
    log_res = supabase.table("notification_logs").insert(log_row).execute()
    log_id = log_res.data[0]["id"]

    try:
        _get_firebase_app()
        fcm_message = messaging.Message(
            notification=messaging.Notification(title=title, body=message),
            topic=topic,
            data={"release_id": release_id, "application_id": application_id},
        )
        messaging.send(fcm_message)
        status_value = "sent"
    except Exception as exc:  # noqa: BLE001
        status_value = "failed"
        supabase.table("notification_logs").update(
            {"status": status_value}
        ).eq("id", log_id).execute()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send FCM notification: {exc}",
        ) from exc

    updated = (
        supabase.table("notification_logs")
        .update({"status": status_value, "sent_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", log_id)
        .execute()
    )
    return updated.data[0]
