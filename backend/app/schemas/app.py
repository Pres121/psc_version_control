from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AppBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    app_key: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    package_name: str = Field(..., min_length=1, max_length=200)
    platform: Literal["android", "ios", "both"] = "both"
    description: str | None = None
    is_active: bool = True


class AppCreate(AppBase):
    pass


class AppUpdate(BaseModel):
    name: str | None = None
    package_name: str | None = None
    platform: Literal["android", "ios", "both"] | None = None
    description: str | None = None
    is_active: bool | None = None


class AppOut(AppBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppWithVersionSummary(AppOut):
    """Used on the dashboard overview: current vs latest version per platform."""
    latest_android_version: str | None = None
    latest_ios_version: str | None = None
