"""Public download APIs for PSC app binaries."""
from fastapi import APIRouter, HTTPException, Query, status

from app.database.supabase_client import get_supabase
from app.schemas.download import DownloadInfoOut
from app.services.storage_service import create_signed_download_url
from app.services.version_service import compare_versions

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("/{app_key}", response_model=DownloadInfoOut)
def get_download_info(
    app_key: str,
    platform: str = Query("android", pattern="^(android|ios)$"),
):
    """Return metadata + a short-lived signed URL for the latest published build."""
    supabase = get_supabase()
    app_res = (
        supabase.table("apps")
        .select("id, name, app_key, is_active")
        .eq("app_key", app_key)
        .limit(1)
        .execute()
    )
    if not app_res.data or not app_res.data[0]["is_active"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    app = app_res.data[0]
    releases_res = (
        supabase.table("releases")
        .select(
            "version, build_number, release_notes, storage_path, file_name, file_size_bytes"
        )
        .eq("application_id", app["id"])
        .eq("platform", platform)
        .eq("is_published", True)
        .not_.is_("storage_path", "null")
        .execute()
    )
    releases = [r for r in (releases_res.data or []) if r.get("storage_path")]
    if not releases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No downloadable build published for this app yet",
        )

    # Pick highest semver; on ties, higher build_number wins.
    latest = releases[0]
    for candidate in releases[1:]:
        cmp = compare_versions(candidate["version"], latest["version"])
        if cmp > 0 or (
            cmp == 0 and int(candidate["build_number"]) > int(latest["build_number"])
        ):
            latest = candidate

    signed = create_signed_download_url(latest["storage_path"])
    return DownloadInfoOut(
        app_key=app["app_key"],
        app_name=app["name"],
        platform=platform,
        version=latest["version"],
        build_number=latest["build_number"],
        file_name=latest.get("file_name"),
        file_size_bytes=latest.get("file_size_bytes"),
        download_url=signed,
        release_notes=latest.get("release_notes") or [],
    )
