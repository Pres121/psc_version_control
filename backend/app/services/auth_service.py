from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt

from app.core.config import get_settings
from app.database.supabase_client import get_supabase

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def authenticate_admin(email: str, password: str) -> dict | None:
    supabase = get_supabase()
    res = (
        supabase.table("admin_users")
        .select("*")
        .eq("email", email)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    user = res.data[0]
    if not verify_password(password, user["hashed_password"]):
        return None

    supabase.table("admin_users").update(
        {"last_login_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", user["id"]).execute()

    return user
