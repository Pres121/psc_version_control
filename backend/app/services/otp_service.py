"""OTP challenge creation and verification for admin login."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.database.supabase_client import get_supabase
from app.services.auth_service import create_access_token, hash_password, verify_password
from app.services.email_service import send_otp_email


def _generate_otp_code(length: int) -> str:
    # Numeric OTP, cryptographically random
    upper = 10**length
    return str(secrets.randbelow(upper)).zfill(length)


def create_login_challenge(user: dict) -> dict:
    """Invalidate prior OTPs, create a new one, email it, return challenge token."""
    settings = get_settings()
    supabase = get_supabase()
    admin_id = user["id"]

    # Invalidate unused OTPs for this admin
    supabase.table("admin_otps").update(
        {"consumed_at": datetime.now(timezone.utc).isoformat()}
    ).eq("admin_user_id", admin_id).is_("consumed_at", "null").execute()

    code = _generate_otp_code(settings.OTP_LENGTH)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    supabase.table("admin_otps").insert(
        {
            "admin_user_id": admin_id,
            "code_hash": hash_password(code),
            "expires_at": expires_at.isoformat(),
            "attempt_count": 0,
        }
    ).execute()

    send_otp_email(to=user["email"], code=code, full_name=user.get("full_name"))

    challenge_token = create_access_token(
        subject=admin_id,
        extra_claims={
            "type": "otp_challenge",
            "role": user.get("role"),
            "email": user.get("email"),
        },
        expire_minutes=settings.OTP_EXPIRE_MINUTES,
    )
    return {
        "otp_required": True,
        "challenge_token": challenge_token,
        "expires_in_minutes": settings.OTP_EXPIRE_MINUTES,
        "message": "A verification code was sent to your email.",
    }


def verify_login_otp(*, challenge_payload: dict, otp: str) -> dict:
    settings = get_settings()
    if challenge_payload.get("type") != "otp_challenge":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid challenge")

    admin_id = challenge_payload.get("sub")
    if not admin_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid challenge")

    supabase = get_supabase()
    otp_res = (
        supabase.table("admin_otps")
        .select("*")
        .eq("admin_user_id", admin_id)
        .is_("consumed_at", "null")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not otp_res.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active verification code")

    row = otp_res.data[0]
    expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification code expired")

    attempts = int(row.get("attempt_count") or 0)
    if attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many invalid attempts")

    if not verify_password(otp.strip(), row["code_hash"]):
        supabase.table("admin_otps").update({"attempt_count": attempts + 1}).eq("id", row["id"]).execute()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification code")

    supabase.table("admin_otps").update(
        {"consumed_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", row["id"]).execute()

    user_res = (
        supabase.table("admin_users")
        .select("id, email, full_name, role, is_active")
        .eq("id", admin_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not user_res.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")

    user = user_res.data[0]
    supabase.table("admin_users").update(
        {"last_login_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", user["id"]).execute()

    token = create_access_token(subject=user["id"], extra_claims={"role": user["role"], "type": "access"})
    return {"access_token": token, "token_type": "bearer"}
