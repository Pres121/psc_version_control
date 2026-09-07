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
    update_url: str
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
    release_title: str | None = None
    release_notes: list[str] | None = None
    minimum_supported_version: str | None = None
    is_mandatory: bool | None = None
    update_url: str | None = None
    is_published: bool | None = None
    release_date: datetime | None = None


class ReleaseOut(ReleaseBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
