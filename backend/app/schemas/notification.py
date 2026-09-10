from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationSendRequest(BaseModel):
    application_id: UUID
    release_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)


class NotificationLogOut(BaseModel):
    id: UUID
    application_id: UUID
    release_id: UUID | None
    title: str
    message: str
    fcm_topic: str
    status: str
    targeted_device_count: int | None
    sent_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceRegisterRequest(BaseModel):
    app_key: str = Field(..., min_length=1, max_length=100)
    platform: str = Field(..., pattern="^(android|ios)$")
    fcm_token: str = Field(..., min_length=10, max_length=4096)
    app_version: str | None = Field(None, max_length=50)
