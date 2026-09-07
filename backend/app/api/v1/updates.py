from fastapi import APIRouter, Request

from app.core.limiter import limiter
from app.schemas.update import UpdateCheckRequest, UpdateCheckResponse
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
    return check_for_update(payload)
