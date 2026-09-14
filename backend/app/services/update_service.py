"""
Business logic for the public update-check endpoint.
Kept out of the route handler per the project's layering convention.
"""
from fastapi import HTTPException, status

from app.database.supabase_client import get_supabase
from app.schemas.update import UpdateCheckRequest, UpdateCheckResponse
from app.services.storage_service import download_page_url
from app.services.version_service import is_greater, is_less, is_valid_semver


def check_for_update(payload: UpdateCheckRequest) -> UpdateCheckResponse:
    supabase = get_supabase()

    # 1. Find the application (must exist and be active)
    app_res = (
        supabase.table("apps")
        .select("id, name, app_key, is_active")
        .eq("app_key", payload.app_key)
        .limit(1)
        .execute()
    )
    if not app_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown app_key")

    app_row = app_res.data[0]
    if not app_row["is_active"]:
        # Treat an inactive/retired app as "no update info" rather than leaking status.
        return UpdateCheckResponse(update_available=False, update_required=False)

    if not is_valid_semver(payload.version):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version format")

    # 2. Find the latest published release for this app/platform.
    releases_res = (
        supabase.table("releases")
        .select(
            "version, build_number, release_title, release_notes, "
            "minimum_supported_version, is_mandatory, update_url, storage_path"
        )
        .eq("application_id", app_row["id"])
        .eq("platform", payload.platform)
        .eq("is_published", True)
        .execute()
    )

    releases = releases_res.data or []
    if not releases:
        return UpdateCheckResponse(update_available=False, update_required=False)

    latest = max(releases, key=lambda r: _version_sort_key(r["version"]))

    update_available = is_greater(latest["version"], payload.version)
    update_required = is_less(payload.version, latest["minimum_supported_version"])

    if not update_available and not update_required:
        return UpdateCheckResponse(update_available=False, update_required=False)

    # Prefer uploaded build download page; fall back to any custom update_url.
    resolved_url = latest.get("update_url")
    if latest.get("storage_path"):
        resolved_url = download_page_url(app_row["app_key"], payload.platform)

    return UpdateCheckResponse(
        update_available=update_available,
        update_required=update_required,
        latest_version=latest["version"],
        latest_build=latest["build_number"],
        minimum_supported_version=latest["minimum_supported_version"],
        title=latest["release_title"] or "New version available",
        message=f"{app_row['name']} has been updated with new features and improvements.",
        release_notes=latest["release_notes"] or [],
        update_url=resolved_url,
    )


def _version_sort_key(version: str):
    from app.services.version_service import parse_version

    major, minor, patch, pre = parse_version(version)
    return (major, minor, patch, pre is None, pre or "")
