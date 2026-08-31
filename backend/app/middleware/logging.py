"""Request logging, timing, and correlation ID middleware."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("panagah.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, duration, and correlation ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:12]
        request.state.correlation_id = correlation_id

        # Start timer
        start = time.perf_counter()

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "request_error",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status": 500,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000

        # Add headers
        response.headers["X-Request-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{duration_ms:.0f}ms"

        # Log
        log_data = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "")[:100],
        }

        if response.status_code >= 500:
            logger.error("request_error", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("request_warn", extra=log_data)
        else:
            logger.info("request_ok", extra=log_data)

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add precise timing headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        # Add timing header
        response.headers["Server-Timing"] = f"total;dur={duration_ms:.0f}"

        return response
