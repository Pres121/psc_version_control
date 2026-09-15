from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from postgrest.exceptions import APIError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import announcements, apps, auth, downloads, logs, notifications, releases, updates
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.security import SecurityHeadersMiddleware
from app.templates.download_page import DOWNLOAD_PAGE_HTML

settings = get_settings()

_enable_docs = settings.DOCS_ENABLED and settings.ENVIRONMENT.lower() != "production"

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Centralized update-management API for PSC Flutter applications. "
        "See /api/v1/updates/check for the public version-check endpoint "
        "used by client apps."
    ),
    docs_url="/docs" if _enable_docs else None,
    redoc_url="/redoc" if _enable_docs else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# credentials=True with allow_origins=["*"] is unsafe — only enable when origins are explicit.
_origins = settings.ALLOWED_ORIGINS
_allow_credentials = "*" not in _origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(APIError)
async def supabase_api_error_handler(request: Request, exc: APIError):
    code = str(getattr(exc, "code", "") or "")
    message = str(getattr(exc, "message", "") or exc).lower()
    if code in {"502", "503", "504"} or "timeout" in message or "gateway" in message:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Database temporarily unavailable. Please try again in a moment."},
        )
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Database request failed. Please try again."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internal details (stack traces, DB errors) to clients.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


app.include_router(updates.router, prefix=settings.API_V1_PREFIX)
app.include_router(announcements.router, prefix=settings.API_V1_PREFIX)
app.include_router(apps.router, prefix=settings.API_V1_PREFIX)
app.include_router(releases.router, prefix=settings.API_V1_PREFIX)
app.include_router(downloads.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(logs.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/download/{app_key}", response_class=HTMLResponse, tags=["downloads"])
def download_landing_page(app_key: str):
    """Branded page opened by Flutter 'Update Now' — auto-starts the APK/IPA download."""
    return HTMLResponse(content=DOWNLOAD_PAGE_HTML)
