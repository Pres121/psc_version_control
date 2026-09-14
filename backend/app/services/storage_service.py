"""
Supabase Storage helpers for PSC app binaries (APK / IPA).

Files live in a private bucket. Clients never get the service key —
they hit the public download page, which requests a short-lived signed URL.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.database.supabase_client import get_supabase

ALLOWED_EXTENSIONS = {".apk", ".aab", ".ipa", ".zip"}
CONTENT_TYPES = {
    ".apk": "application/vnd.android.package-archive",
    ".aab": "application/octet-stream",
    ".ipa": "application/octet-stream",
    ".zip": "application/zip",
}


def _safe_ext(filename: str) -> str:
    ext = PurePosixPath(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext or '(none)'}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return ext


def _sanitize_segment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "app"


def build_storage_paths(app_key: str, platform: str, version: str, build_number: int, filename: str) -> tuple[str, str]:
    """Return (latest_path, versioned_path). latest_path is overwritten on each upload."""
    ext = _safe_ext(filename)
    app_key = _sanitize_segment(app_key)
    platform = _sanitize_segment(platform)
    version = _sanitize_segment(version)
    latest = f"apps/{app_key}/{platform}/latest{ext}"
    versioned = f"apps/{app_key}/{platform}/{version}-b{build_number}{ext}"
    return latest, versioned


def download_page_url(app_key: str, platform: str) -> str:
    settings = get_settings()
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/download/{app_key}?platform={platform}"


async def upload_app_binary(
    *,
    app_key: str,
    platform: str,
    version: str,
    build_number: int,
    file: UploadFile,
) -> dict:
    settings = get_settings()
    filename = file.filename or f"app-{platform}.apk"
    ext = _safe_ext(filename)
    content_type = file.content_type or CONTENT_TYPES.get(ext, "application/octet-stream")
    latest_path, versioned_path = build_storage_paths(
        app_key, platform, version, build_number, filename
    )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(data) > 524288000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 500 MB limit")

    supabase = get_supabase()
    bucket = supabase.storage.from_(settings.STORAGE_BUCKET)
    options = {"content-type": content_type, "upsert": "true"}

    try:
        bucket.upload(latest_path, data, file_options=options)
        bucket.upload(versioned_path, data, file_options=options)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload to storage: {exc}",
        ) from exc

    return {
        "storage_path": latest_path,
        "versioned_path": versioned_path,
        "file_name": PurePosixPath(filename).name,
        "file_size_bytes": len(data),
        "content_type": content_type,
        "update_url": download_page_url(app_key, platform),
    }


def create_signed_download_url(storage_path: str) -> str:
    settings = get_settings()
    try:
        res = (
            get_supabase()
            .storage.from_(settings.STORAGE_BUCKET)
            .create_signed_url(storage_path, settings.SIGNED_URL_EXPIRE_SECONDS)
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create download link: {exc}",
        ) from exc

    # supabase-py may return dict with signedURL / signedUrl
    if isinstance(res, dict):
        url = res.get("signedURL") or res.get("signedUrl") or res.get("signed_url")
        if url:
            return url
    if isinstance(res, str):
        return res
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Storage did not return a signed download URL",
    )
