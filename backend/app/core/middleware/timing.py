import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware.timing")


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that tracks the time taken to process an HTTP request
    and sets the 'X-Process-Time' header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.6f}s"

        # Log request paths excluding documentation and health checks
        if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            request_id = getattr(request.state, "request_id", "unknown")
            logger.info(
                f"Request {request.method} {request.url.path} completed in {process_time:.6f}s [ID: {request_id}]"
            )
        return response
