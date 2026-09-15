from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.version_service import is_valid_semver


class ReleaseBase(BaseModel):
    application_id: UUID
    platform: Literal["android", "ios"]
    version: str = Field(..., min_length=1, max_length=50)
    build_number: int = Field(..., ge=1)
    release_title: str | None = None
    release_notes: list[str] = Field(default_factory=list)
    minimum_supported_version: str = Field(..., min_length=1, max_length=50)
    is_mandatory: bool = False
    update_url: str | None = None
    is_published: bool = False
    release_date: datetime | None = None

    @field_validator("version", "minimum_supported_version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        if not is_valid_semver(v):
            raise ValueError(f"'{v}' is not a valid semantic version (expected e.g. 1.2.3)")
        return v


class ReleaseCreate(ReleaseBase):
    pass


class ReleaseUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=50)
    build_number: int | None = Field(default=None, ge=1)
    release_title: str | None = None
    release_notes: list[str] | None = None
    minimum_supported_version: str | None = None
    is_mandatory: bool | None = None
    update_url: str | None = None
    is_published: bool | None = None
    release_date: datetime | None = None

    @field_validator("version", "minimum_supported_version")
    @classmethod
    def validate_optional_semver(cls, v: str | None) -> str | None:
        if v is not None and not is_valid_semver(v):
            raise ValueError(f"'{v}' is not a valid semantic version (expected e.g. 1.2.3)")
        return v


class ReleaseVerification(BaseModel):
    """Confirm sensitive release actions by re-entering the app key only."""
    app_key: str = Field(..., min_length=1, max_length=100)


class VerifiedReleaseUpdate(ReleaseUpdate, ReleaseVerification):
    pass


class ReleaseOut(ReleaseBase):
    id: UUID
    storage_path: str | None = None
    file_name: str | None = None
    file_size_bytes: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReleaseUploadUrlRequest(BaseModel):
    """Admin asks backend for short-lived Supabase signed upload URLs."""

    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., ge=1, le=524288000)


class SignedUploadTarget(BaseModel):
    path: str
    token: str
    signed_url: str


class ReleaseUploadUrlResponse(BaseModel):
    storage_path: str
    versioned_path: str
    file_name: str
    file_size_bytes: int
    content_type: str
    uploads: list[SignedUploadTarget]


class ReleaseUploadCompleteRequest(BaseModel):
    """Confirm browser finished direct-to-Supabase upload; persist release metadata."""

    storage_path: str = Field(..., min_length=1, max_length=500)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., ge=1, le=524288000)
