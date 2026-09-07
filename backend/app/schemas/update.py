from typing import Literal

from pydantic import BaseModel, Field


class UpdateCheckRequest(BaseModel):
    app_key: str = Field(..., min_length=1, max_length=100)
    platform: Literal["android", "ios"]
    version: str = Field(..., min_length=1, max_length=50)
    build_number: int = Field(..., ge=0)


class UpdateCheckResponse(BaseModel):
    update_available: bool
    update_required: bool
    latest_version: str | None = None
    latest_build: int | None = None
    minimum_supported_version: str | None = None
    title: str | None = None
    message: str | None = None
    release_notes: list[str] | None = None
    update_url: str | None = None
