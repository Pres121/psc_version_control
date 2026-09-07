from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_admin
from app.schemas.auth import AdminUserOut, LoginRequest, TokenResponse
from app.services.auth_service import authenticate_admin, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_admin(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(subject=user["id"], extra_claims={"role": user["role"]})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AdminUserOut)
def me(admin: dict = Depends(get_current_admin)):
    return admin
