from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.auth.dependencies import get_current_admin
from app.core.limiter import limiter
from app.schemas.announcement import (
    AnnouncementAdminOut,
    AnnouncementCheckRequest,
    AnnouncementCheckResponse,
    AnnouncementCreateRequest,
)
from app.services.announcement_service import (
    check_announcement,
    create_announcement,
    deactivate_announcement,
    list_announcements,
)

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.post("/check", response_model=AnnouncementCheckResponse)
@limiter.limit("60/minute")
def check_in_app_announcement(
    request: Request, payload: AnnouncementCheckRequest
) -> AnnouncementCheckResponse:
    """Public: Flutter apps poll this on launch for an in-app message."""
    return check_announcement(payload)


@router.post("/", response_model=AnnouncementAdminOut, status_code=201)
def create_in_app_announcement(
    payload: AnnouncementCreateRequest, admin: dict = Depends(get_current_admin)
):
    return create_announcement(payload)


@router.get("/", response_model=list[AnnouncementAdminOut])
def list_in_app_announcements(
    application_id: UUID | None = None, admin: dict = Depends(get_current_admin)
):
    return list_announcements(str(application_id) if application_id else None)


@router.post("/{announcement_id}/deactivate", response_model=AnnouncementAdminOut)
def deactivate_in_app_announcement(
    announcement_id: UUID, admin: dict = Depends(get_current_admin)
):
    return deactivate_announcement(str(announcement_id))
