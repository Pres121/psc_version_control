from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnnouncementCheckRequest(BaseModel):
    app_key: str = Field(..., min_length=1, max_length=100)


class AnnouncementOut(BaseModel):
    id: UUID
    title: str
    message: str
    release_id: UUID | None = None
    created_at: datetime | None = None


class AnnouncementCheckResponse(BaseModel):
    has_announcement: bool
    announcement: AnnouncementOut | None = None


class AnnouncementCreateRequest(BaseModel):
    application_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    release_id: UUID | None = None


class AnnouncementAdminOut(BaseModel):
    id: UUID
    application_id: UUID
    release_id: UUID | None = None
    title: str
    message: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
