from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import apps, auth, logs, notifications, releases, updates
from app.core.config import get_settings
from app.core.limiter import limiter

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Centralized update-management API for PSC Flutter applications. "
        "See /api/v1/updates/check for the public version-check endpoint "
        "used by client apps."
    ),
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internal details (stack traces, DB errors) to clients.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


app.include_router(updates.router, prefix=settings.API_V1_PREFIX)
app.include_router(apps.router, prefix=settings.API_V1_PREFIX)
app.include_router(releases.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(logs.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
