from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin
from app.database.supabase_client import get_supabase
from app.schemas.release import ReleaseCreate, ReleaseOut, ReleaseUpdate

router = APIRouter(prefix="/releases", tags=["releases"])


@router.get("", response_model=list[ReleaseOut])
def list_releases(
    application_id: UUID | None = None,
    platform: str | None = None,
    admin: dict = Depends(get_current_admin),
):
    supabase = get_supabase()
    query = supabase.table("releases").select("*")
    if application_id:
        query = query.eq("application_id", str(application_id))
    if platform:
        query = query.eq("platform", platform)
    res = query.order("created_at", desc=True).execute()
    return res.data


@router.post("", response_model=ReleaseOut, status_code=status.HTTP_201_CREATED)
def create_release(payload: ReleaseCreate, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()

    app_res = supabase.table("apps").select("id").eq("id", str(payload.application_id)).execute()
    if not app_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    body = payload.model_dump(mode="json")
    body["application_id"] = str(payload.application_id)
    res = supabase.table("releases").insert(body).execute()
    return res.data[0]


@router.get("/{release_id}", response_model=ReleaseOut)
def get_release(release_id: UUID, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    res = supabase.table("releases").select("*").eq("id", str(release_id)).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]


@router.patch("/{release_id}", response_model=ReleaseOut)
def update_release(release_id: UUID, payload: ReleaseUpdate, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    updates = {k: v for k, v in payload.model_dump(mode="json").items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    res = supabase.table("releases").update(updates).eq("id", str(release_id)).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]


@router.post("/{release_id}/publish", response_model=ReleaseOut)
def publish_release(release_id: UUID, admin: dict = Depends(get_current_admin)):
    """Explicit publish action, so the dashboard can show a confirmation step
    before a release goes live to all client apps."""
    supabase = get_supabase()
    res = (
        supabase.table("releases")
        .update({"is_published": True})
        .eq("id", str(release_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]
