from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
