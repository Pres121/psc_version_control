from fastapi import APIRouter, HTTPException, Request

from app.core.limiter import limiter
from app.schemas.update import UpdateCheckRequest, UpdateCheckResponse
from app.services.log_service import log_request_event
from app.services.update_service import check_for_update

router = APIRouter(prefix="/updates", tags=["updates"])


@router.post("/check", response_model=UpdateCheckResponse)
@limiter.limit("60/minute")
def check_update(request: Request, payload: UpdateCheckRequest) -> UpdateCheckResponse:
    """
    Public endpoint used by all PSC Flutter apps to check whether an
    update is available. Intentionally exposes only the minimum fields
    a client needs - no internal IDs, no admin data, no other app's info.
    """
    try:
        response = check_for_update(payload)
    except HTTPException as exc:
        log_request_event(
            event_type="update_check",
            request=request,
            app_key=payload.app_key,
            platform=payload.platform,
            app_version=payload.version,
            build_number=payload.build_number,
            result=f"error_{exc.status_code}",
            metadata={"detail": str(exc.detail)},
        )
        raise

    if response.update_required:
        result = "update_required"
    elif response.update_available:
        result = "update_available"
    else:
        result = "no_update"

    log_request_event(
        event_type="update_check",
        request=request,
        app_key=payload.app_key,
        platform=payload.platform,
        app_version=payload.version,
        build_number=payload.build_number,
        result=result,
        metadata={
            "latest_version": response.latest_version,
            "update_available": response.update_available,
            "update_required": response.update_required,
        },
    )
    return response
