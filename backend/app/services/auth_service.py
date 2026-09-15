from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt

from app.core.config import get_settings
from app.database.supabase_client import get_supabase


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:  # noqa: BLE001
        return False


def create_access_token(
    subject: str,
    extra_claims: dict | None = None,
    expire_minutes: int | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    minutes = expire_minutes if expire_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = now + timedelta(minutes=minutes)
    to_encode = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str, *, expected_type: str | None = "access") -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        token_type = payload.get("type", "access")
        if expected_type is not None and token_type != expected_type:
            return None
        return payload
    except JWTError:
        return None


def authenticate_admin(email: str, password: str) -> dict | None:
    supabase = get_supabase()
    # Normalize email to reduce duplicate-account style login surprises
    normalized = email.strip().lower()
    res = (
        supabase.table("admin_users")
        .select("*")
        .eq("email", normalized)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not res.data:
        # Fallback: legacy rows may have mixed-case emails
        res = (
            supabase.table("admin_users")
            .select("*")
            .ilike("email", normalized)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
    if not res.data:
        return None
    user = res.data[0]
    if not verify_password(password, user["hashed_password"]):
        return None

    return user
