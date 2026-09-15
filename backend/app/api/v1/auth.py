import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_admin, require_superadmin
from app.core.config import get_settings
from app.core.limiter import limiter
from app.database.supabase_client import get_supabase
from app.schemas.auth import (
    AdminCreateRequest,
    AdminCreateResponse,
    AdminUpdateRequest,
    AdminUserOut,
    LoginRequest,
    OtpChallengeResponse,
    TokenResponse,
    VerifyOtpRequest,
)
from app.services.auth_service import (
    authenticate_admin,
    decode_access_token,
    hash_password,
)
from app.services.email_service import send_admin_invite_email
from app.services.otp_service import create_login_challenge, verify_login_otp

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=OtpChallengeResponse)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, payload: LoginRequest):
    """Step 1: validate password, then email a one-time code."""
    user = authenticate_admin(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return create_login_challenge(user)


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def verify_otp(request: Request, payload: VerifyOtpRequest):
    """Step 2: verify email OTP and issue the admin session JWT."""
    challenge = decode_access_token(payload.challenge_token, expected_type="otp_challenge")
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification session",
        )
    return verify_login_otp(challenge_payload=challenge, otp=payload.otp)


@router.get("/me", response_model=AdminUserOut)
def me(admin: dict = Depends(get_current_admin)):
    return admin


@router.get("/admins", response_model=list[AdminUserOut])
def list_admins(admin: dict = Depends(require_superadmin)):
    supabase = get_supabase()
    res = (
        supabase.table("admin_users")
        .select("id, email, full_name, role, is_active")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.post("/admins", response_model=AdminCreateResponse, status_code=201)
def create_admin(payload: AdminCreateRequest, admin: dict = Depends(require_superadmin)):
    supabase = get_supabase()
    email = str(payload.email).strip().lower()
    existing = supabase.table("admin_users").select("id").eq("email", email).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An admin with this email already exists")

    temporary_password = payload.password or secrets.token_urlsafe(12)
    row = {
        "email": email,
        "hashed_password": hash_password(temporary_password),
        "full_name": payload.full_name,
        "role": payload.role,
        "is_active": True,
    }
    res = supabase.table("admin_users").insert(row).execute()
    created = res.data[0]
    admin_out = AdminUserOut(
        id=created["id"],
        email=created["email"],
        full_name=created.get("full_name"),
        role=created["role"],
        is_active=created["is_active"],
    )

    email_sent = False
    try:
        send_admin_invite_email(
            to=email,
            full_name=payload.full_name,
            temporary_password=temporary_password,
            role=payload.role,
        )
        email_sent = True
    except HTTPException:
        # Account still created; superadmin can share password manually.
        email_sent = False

    return AdminCreateResponse(
        admin=admin_out,
        temporary_password=None if email_sent else temporary_password,
        email_sent=email_sent,
    )


@router.patch("/admins/{admin_id}", response_model=AdminUserOut)
def update_admin(
    admin_id: str,
    payload: AdminUpdateRequest,
    admin: dict = Depends(require_superadmin),
):
    if admin_id == admin["id"] and payload.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate yourself")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    supabase = get_supabase()
    res = (
        supabase.table("admin_users")
        .update(updates)
        .eq("id", admin_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    row = res.data[0]
    return AdminUserOut(
        id=row["id"],
        email=row["email"],
        full_name=row.get("full_name"),
        role=row["role"],
        is_active=row["is_active"],
    )
