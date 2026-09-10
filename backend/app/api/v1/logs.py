from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_admin
from app.database.supabase_client import get_supabase
from app.schemas.log import RequestLogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[RequestLogOut])
def list_request_logs(
    event_type: str | None = Query(None, description="update_check | device_register"),
    app_key: str | None = None,
    application_id: UUID | None = None,
    ip_address: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    admin: dict = Depends(get_current_admin),
):
    """Admin-only activity feed: update checks, device registrations, IPs."""
    supabase = get_supabase()
    query = supabase.table("request_logs").select("*")

    if event_type:
        query = query.eq("event_type", event_type)
    if app_key:
        query = query.eq("app_key", app_key)
    if application_id:
        query = query.eq("application_id", str(application_id))
    if ip_address:
        query = query.eq("ip_address", ip_address)

    res = query.order("created_at", desc=True).limit(limit).execute()
    return res.data or []
