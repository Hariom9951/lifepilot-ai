from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds default security headers to every response to protect
    against XSS, Clickjacking, and other code injection exploits.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Relax CSP for docs to load Swagger UI CDNs
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
            )

        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response
