from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnnouncementCheckRequest(BaseModel):
    app_key: str = Field(..., min_length=1, max_length=100)


class AnnouncementOut(BaseModel):
    id: UUID
    title: str
    message: str
    created_at: datetime | None = None


class AnnouncementCheckResponse(BaseModel):
    has_announcement: bool
    announcement: AnnouncementOut | None = None


class AnnouncementCreateRequest(BaseModel):
    application_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)


class AnnouncementAdminOut(BaseModel):
    id: UUID
    application_id: UUID
    title: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
