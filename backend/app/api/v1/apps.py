from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin
from app.database.supabase_client import get_supabase
from app.schemas.app import AppCreate, AppOut, AppUpdate

router = APIRouter(prefix="/apps", tags=["apps"])


@router.get("", response_model=list[AppOut])
def list_apps(admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    res = supabase.table("apps").select("*").order("created_at", desc=True).execute()
    return res.data


@router.post("", response_model=AppOut, status_code=status.HTTP_201_CREATED)
def create_app(payload: AppCreate, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    existing = supabase.table("apps").select("id").eq("app_key", payload.app_key).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="app_key already exists")

    res = supabase.table("apps").insert(payload.model_dump()).execute()
    return res.data[0]


@router.get("/{app_id}", response_model=AppOut)
def get_app(app_id: UUID, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    res = supabase.table("apps").select("*").eq("id", str(app_id)).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    return res.data[0]


@router.patch("/{app_id}", response_model=AppOut)
def update_app(app_id: UUID, payload: AppUpdate, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    res = supabase.table("apps").update(updates).eq("id", str(app_id)).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    return res.data[0]


@router.get("/{app_id}/releases", response_model=list[dict])
def app_release_history(app_id: UUID, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    res = (
        supabase.table("releases")
        .select("*")
        .eq("application_id", str(app_id))
        .order("created_at", desc=True)
        .execute()
    )
    return res.data
