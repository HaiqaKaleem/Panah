"""Advanced rate limiting middleware with sliding window algorithm."""

import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ── Rate Limit Tiers ──────────────────────────────────────────────────
RATE_TIERS = {
    "anonymous": {
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "burst": 10,  # Max requests in 1 second
    },
    "free": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "burst": 20,
    },
    "pro": {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "burst": 50,
    },
    "enterprise": {
        "requests_per_minute": 1000,
        "requests_per_hour": 50000,
        "burst": 200,
    },
}

# ── Endpoint-Specific Limits ──────────────────────────────────────────
ENDPOINT_LIMITS = {
    "/api/v1/auth/login": {"requests_per_minute": 5, "burst": 2},
    "/api/v1/auth/register": {"requests_per_minute": 3, "burst": 1},
    "/api/v1/engineering/generate-report": {"requests_per_minute": 10, "burst": 3},
    "/api/v1/platform/webhooks/test": {"requests_per_minute": 5, "burst": 2},
}


class SlidingWindowRateLimiter:
    """Sliding window rate limiter using in-memory storage."""

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._burst_windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, dict]:
        """Check if request is allowed within the rate limit."""
        now = time.time()
        window_start = now - window_seconds

        # Clean old entries
        self._windows[key] = [t for t in self._windows[key] if t > window_start]
        self._burst_windows[key] = [t for t in self._burst_windows[key] if t > now - 1]

        current_count = len(self._windows[key])
        burst_count = len(self._burst_windows[key])

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - current_count - 1)),
            "X-RateLimit-Reset": str(int(window_start + window_seconds)),
        }

        if current_count >= limit:
            retry_after = self._windows[key][0] + window_seconds - now if self._windows[key] else 1
            headers["Retry-After"] = str(int(retry_after) + 1)
            return False, headers

        # Record request
        self._windows[key].append(now)
        self._burst_windows[key].append(now)

        return True, headers

    def get_usage(self, key: str, window_seconds: int = 60) -> dict:
        """Get current usage statistics."""
        now = time.time()
        window_start = now - window_seconds
        self._windows[key] = [t for t in self._windows[key] if t > window_start]

        return {
            "requests": len(self._windows[key]),
            "window_seconds": window_seconds,
        }


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with tier-based and endpoint-specific limits."""

    def __init__(self, app, default_tier: str = "anonymous"):
        super().__init__(app)
        self.default_tier = default_tier

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for docs, health, and testing
        path = request.url.path
        import os
        if os.getenv("ENVIRONMENT") == "testing" or path in ("/docs", "/redoc", "/openapi.json", "/health", "/metrics", "/"):
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key")
        tier = self._get_tier(request)

        # Build rate limit key
        if api_key:
            key = f"apikey:{api_key}:{path}"
        else:
            key = f"ip:{client_ip}:{path}"

        # Check endpoint-specific limits first
        if path in ENDPOINT_LIMITS:
            ep_limit = ENDPOINT_LIMITS[path]
            allowed, headers = rate_limiter.is_allowed(
                f"ep:{key}",
                limit=ep_limit.get("requests_per_minute", 10),
                window_seconds=60,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Endpoint rate limit exceeded. Try again in {headers.get('Retry-After', 60)} seconds.",
                        "retry_after": int(headers.get("Retry-After", 60)),
                    },
                    headers=headers,
                )

        # Check tier-based limits
        tier_config = RATE_TIERS.get(tier, RATE_TIERS["anonymous"])
        allowed, headers = rate_limiter.is_allowed(
            f"tier:{key}",
            limit=tier_config["requests_per_minute"],
            window_seconds=60,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded for {tier} tier. Upgrade your plan for higher limits.",
                    "tier": tier,
                    "retry_after": int(headers.get("Retry-After", 60)),
                    "upgrade_url": "/api/v1/platform/api-keys",
                },
                headers=headers,
            )

        # Add rate limit headers to response
        response = await call_next(request)
        for key_name, value in headers.items():
            response.headers[key_name] = value

        return response

    def _get_tier(self, request: Request) -> str:
        """Determine rate limit tier from request."""
        # Check for API key tier header
        tier_header = request.headers.get("X-RateLimit-Tier")
        if tier_header and tier_header in RATE_TIERS:
            return tier_header

        # Check for API key (default to free)
        if request.headers.get("X-API-Key"):
            return "free"

        return self.default_tier
