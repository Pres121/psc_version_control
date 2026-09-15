from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpChallengeResponse(BaseModel):
    otp_required: bool = True
    challenge_token: str
    expires_in_minutes: int
    message: str


class VerifyOtpRequest(BaseModel):
    challenge_token: str = Field(..., min_length=20)
    otp: str = Field(..., min_length=4, max_length=12)


class AdminUserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool


class AdminCreateRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(None, max_length=120)
    role: str = Field("admin", pattern="^(admin|superadmin)$")
    password: str | None = Field(None, min_length=8, max_length=128)


class AdminUpdateRequest(BaseModel):
    full_name: str | None = Field(None, max_length=120)
    role: str | None = Field(None, pattern="^(admin|superadmin)$")
    is_active: bool | None = None


class AdminCreateResponse(BaseModel):
    admin: AdminUserOut
    temporary_password: str | None = None
    email_sent: bool = False
