"""API versioning middleware with deprecation support and version negotiation."""

from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# ── Version Registry ──────────────────────────────────────────────────
API_VERSIONS = {
    "v1": {
        "status": "stable",
        "released": "2026-08-22",
        "sunset": None,
        "description": "Initial production release",
    },
    "v2": {
        "status": "development",
        "released": None,
        "sunset": None,
        "description": "Next version with enhanced features",
    },
}

DEPRECATED_ENDPOINTS = {
    "/api/v1/old-endpoint": {
        "deprecated_in": "v1",
        "removed_in": "v3",
        "alternative": "/api/v1/new-endpoint",
        "sunset_date": "2027-01-01",
    },
}


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API version detection, header injection, and deprecation warnings."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Detect version from path
        path = request.url.path
        detected_version = None
        for version in API_VERSIONS:
            if f"/api/{version}/" in path:
                detected_version = version
                break

        # Process request
        response = await call_next(request)

        # Add version headers
        response.headers["X-API-Version"] = detected_version or "v1"
        response.headers["X-API-Status"] = API_VERSIONS.get(detected_version or "v1", {}).get("status", "unknown")

        # Check if endpoint is deprecated
        for dep_path, dep_info in DEPRECATED_ENDPOINTS.items():
            if dep_path in path:
                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = dep_info.get("sunset_date", "")
                response.headers["X-Deprecation-Info"] = dep_info.get("alternative", "")
                if response.status_code == 200:
                    response.status_code = 200  # Keep 200 but add headers

        # Add CORS headers for versioning
        response.headers["Access-Control-Expose-Headers"] = (
            "X-API-Version, X-API-Status, Deprecation, Sunset, X-Deprecation-Info"
        )

        return response


# ── Version Info Endpoint ─────────────────────────────────────────────

def get_version_info() -> dict:
    """Get API version information."""
    return {
        "current_version": "v1",
        "versions": API_VERSIONS,
        "deprecated_endpoints": DEPRECATED_ENDPOINTS,
        "versioning_scheme": "URI-based (/api/v1/, /api/v2/)",
        "negotiation": "Accept-Version header or URI path",
    }
