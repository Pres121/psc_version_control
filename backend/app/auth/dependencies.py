from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database.supabase_client import get_supabase
from app.services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_admin(token: str | None = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    supabase = get_supabase()
    res = (
        supabase.table("admin_users")
        .select("id, email, full_name, role, is_active")
        .eq("id", payload["sub"])
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise credentials_exception

    return res.data[0]


async def require_superadmin(admin: dict = Depends(get_current_admin)) -> dict:
    if admin.get("role") != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin access required")
    return admin
