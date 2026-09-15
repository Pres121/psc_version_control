"""
Security middleware and helpers: headers, origin checks, path validation.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        # API responses are JSON/HTML download page only — no need for broad CSP on API,
        # but tighten for the download landing page when served as HTML.
        if "text/html" in (response.headers.get("content-type") or ""):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
            )
        return response
