from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_admin
from app.database.supabase_client import get_supabase
from app.schemas.release import (
    ReleaseCreate,
    ReleaseOut,
    ReleaseUploadCompleteRequest,
    ReleaseUploadUrlRequest,
    ReleaseUploadUrlResponse,
    ReleaseVerification,
    VerifiedReleaseUpdate,
)
from app.services.storage_service import (
    create_direct_upload_plan,
    finalize_direct_upload,
    upload_app_binary,
)
from app.services.version_service import compare_versions

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

    existing_res = (
        supabase.table("releases")
        .select("version, build_number")
        .eq("application_id", str(payload.application_id))
        .eq("platform", payload.platform)
        .execute()
    )
    existing_releases = existing_res.data or []
    _validate_release_sequence(payload.version, payload.build_number, existing_releases)

    body = payload.model_dump(mode="json")
    body["application_id"] = str(payload.application_id)
    res = supabase.table("releases").insert(body).execute()
    return res.data[0]


def _validate_release_sequence(version: str, build_number: int, existing_releases: list[dict]) -> None:
    """Keep versions and build numbers monotonic per app/platform."""
    if not existing_releases:
        return

    if any(release["version"] == version for release in existing_releases):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version {version} already exists for this application and platform",
        )

    latest_version = existing_releases[0]["version"]
    for release in existing_releases[1:]:
        if compare_versions(release["version"], latest_version) > 0:
            latest_version = release["version"]

    if compare_versions(version, latest_version) < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version must be higher than the existing version {latest_version}",
        )

    highest_build = max(int(release["build_number"]) for release in existing_releases)
    if build_number <= highest_build:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Build number must be higher than the existing build {highest_build}",
        )


@router.get("/{release_id}", response_model=ReleaseOut)
def get_release(release_id: UUID, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    res = supabase.table("releases").select("*").eq("id", str(release_id)).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]


def _release_with_app(release_id: UUID) -> tuple[dict, dict]:
    supabase = get_supabase()
    release_res = supabase.table("releases").select("*").eq("id", str(release_id)).limit(1).execute()
    if not release_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    release = release_res.data[0]
    app_res = (
        supabase.table("apps")
        .select("app_key")
        .eq("id", release["application_id"])
        .limit(1)
        .execute()
    )
    if not app_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return release, app_res.data[0]


@router.post("/{release_id}/upload-url", response_model=ReleaseUploadUrlResponse)
def create_release_upload_url(
    release_id: UUID,
    payload: ReleaseUploadUrlRequest,
    admin: dict = Depends(get_current_admin),
):
    """Return signed Supabase upload URLs so the browser uploads the binary directly."""
    release, app = _release_with_app(release_id)
    return create_direct_upload_plan(
        app_key=app["app_key"],
        platform=release["platform"],
        version=release["version"],
        build_number=release["build_number"],
        file_name=payload.file_name,
        file_size_bytes=payload.file_size_bytes,
    )


@router.post("/{release_id}/upload-complete", response_model=ReleaseOut)
def complete_release_upload(
    release_id: UUID,
    payload: ReleaseUploadCompleteRequest,
    admin: dict = Depends(get_current_admin),
):
    """Persist release file metadata after a successful direct-to-Supabase upload."""
    release, app = _release_with_app(release_id)
    finalized = finalize_direct_upload(
        app_key=app["app_key"],
        platform=release["platform"],
        version=release["version"],
        build_number=release["build_number"],
        storage_path=payload.storage_path,
        file_name=payload.file_name,
        file_size_bytes=payload.file_size_bytes,
    )
    updated = (
        get_supabase()
        .table("releases")
        .update(finalized)
        .eq("id", str(release_id))
        .execute()
    )
    if not updated.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return updated.data[0]


@router.post("/{release_id}/upload", response_model=ReleaseOut)
async def upload_release_binary(
    release_id: UUID,
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
):
    """Legacy proxy upload (slow on small hosts). Prefer /upload-url + direct Supabase PUT."""
    release, app = _release_with_app(release_id)

    uploaded = await upload_app_binary(
        app_key=app["app_key"],
        platform=release["platform"],
        version=release["version"],
        build_number=release["build_number"],
        file=file,
    )

    updated = (
        get_supabase()
        .table("releases")
        .update(
            {
                "storage_path": uploaded["storage_path"],
                "file_name": uploaded["file_name"],
                "file_size_bytes": uploaded["file_size_bytes"],
                "update_url": uploaded["update_url"],
            }
        )
        .eq("id", str(release_id))
        .execute()
    )
    if not updated.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return updated.data[0]


@router.patch("/{release_id}", response_model=ReleaseOut)
def update_release(release_id: UUID, payload: VerifiedReleaseUpdate, admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()
    release, _ = _verify_release_action(supabase, release_id, payload)
    updates = {
        key: getattr(payload, key)
        for key in payload.model_fields_set
        if key not in {"app_key"}
    }
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if {"version", "build_number"} & updates.keys():
        candidate_version = updates.get("version", release["version"])
        candidate_build = updates.get("build_number", release["build_number"])
        other_releases = (
            supabase.table("releases")
            .select("id, version, build_number")
            .eq("application_id", release["application_id"])
            .eq("platform", release["platform"])
            .execute()
            .data
            or []
        )
        _validate_release_sequence(
            candidate_version,
            candidate_build,
            [item for item in other_releases if item["id"] != str(release_id)],
        )

    res = supabase.table("releases").update(updates).eq("id", str(release_id)).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]


@router.post("/{release_id}/publish", response_model=ReleaseOut)
def publish_release(
    release_id: UUID,
    verification: ReleaseVerification,
    admin: dict = Depends(get_current_admin),
):
    """Explicit publish action, so the dashboard can show a confirmation step
    before a release goes live to all client apps."""
    supabase = get_supabase()
    _verify_release_action(supabase, release_id, verification)
    res = (
        supabase.table("releases")
        .update({"is_published": True})
        .eq("id", str(release_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]


@router.post("/{release_id}/unpublish", response_model=ReleaseOut)
def unpublish_release(
    release_id: UUID,
    verification: ReleaseVerification,
    admin: dict = Depends(get_current_admin),
):
    supabase = get_supabase()
    _verify_release_action(supabase, release_id, verification)
    res = supabase.table("releases").update({"is_published": False}).eq("id", str(release_id)).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    return res.data[0]


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_release(
    release_id: UUID,
    verification: ReleaseVerification,
    admin: dict = Depends(get_current_admin),
):
    supabase = get_supabase()
    _verify_release_action(supabase, release_id, verification)
    res = supabase.table("releases").delete().eq("id", str(release_id)).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")


def _verify_release_action(supabase, release_id: UUID, verification: ReleaseVerification) -> tuple[dict, dict]:
    release_res = supabase.table("releases").select("*").eq("id", str(release_id)).limit(1).execute()
    if not release_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    release = release_res.data[0]
    app_res = supabase.table("apps").select("app_key").eq("id", release["application_id"]).limit(1).execute()
    if not app_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    app = app_res.data[0]

    if verification.app_key != app["app_key"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verification failed. Re-enter the app key exactly to confirm.",
        )
    return release, app
