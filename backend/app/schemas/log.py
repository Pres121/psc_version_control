from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RequestLogOut(BaseModel):
    id: UUID
    event_type: Literal["update_check", "device_register"]
    application_id: UUID | None = None
    app_key: str | None = None
    platform: str | None = None
    app_version: str | None = None
    build_number: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    result: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True
