"""Application Performance Monitoring (APM) middleware — request tracing, error tracking, and metrics."""

import time
import traceback
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class APMMiddleware(BaseHTTPMiddleware):
    """Application Performance Monitoring middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "requests": defaultdict(int),
            "errors": defaultdict(int),
            "response_times": defaultdict(list),
            "status_codes": defaultdict(int),
            "endpoints": defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0}),
        }
        self.start_time = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start = time.perf_counter()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            # Record metrics
            self.metrics["requests"][method] += 1
            self.metrics["status_codes"][response.status_code] += 1
            self.metrics["response_times"][path].append(duration_ms)
            self.metrics["endpoints"][f"{method} {path}"]["count"] += 1
            self.metrics["endpoints"][f"{method} {path}"]["total_time"] += duration_ms

            if response.status_code >= 400:
                self.metrics["errors"][response.status_code] += 1
                self.metrics["endpoints"][f"{method} {path}"]["errors"] += 1

            # Add APM headers
            response.headers["X-APM-Duration"] = f"{duration_ms:.0f}ms"
            response.headers["X-APM-Status"] = "error" if response.status_code >= 400 else "ok"

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            self.metrics["errors"]["500"] += 1
            self.metrics["endpoints"][f"{method} {path}"]["errors"] += 1
            raise

    def get_metrics(self) -> dict:
        """Get comprehensive APM metrics."""
        uptime = time.time() - self.start_time

        # Calculate averages
        avg_response_times = {}
        for path, times in self.metrics["response_times"].items():
            if times:
                avg_response_times[path] = {
                    "avg_ms": round(sum(times) / len(times), 2),
                    "p50_ms": round(sorted(times)[len(times) // 2], 2) if times else 0,
                    "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2) if times else 0,
                    "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 2) if times else 0,
                    "min_ms": round(min(times), 2),
                    "max_ms": round(max(times), 2),
                    "count": len(times),
                }

        # Slowest endpoints
        slowest = sorted(
            avg_response_times.items(),
            key=lambda x: x[1]["avg_ms"],
            reverse=True,
        )[:10]

        # Most error-prone endpoints
        error_prone = sorted(
            [(k, v) for k, v in self.metrics["endpoints"].items() if v["errors"] > 0],
            key=lambda x: x[1]["errors"],
            reverse=True,
        )[:10]

        # Error rate
        total_requests = sum(self.metrics["requests"].values())
        total_errors = sum(self.metrics["errors"].values())
        error_rate = round(total_errors / max(total_requests, 1) * 100, 2)

        return {
            "uptime_seconds": round(uptime, 1),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_percent": error_rate,
            "requests_by_method": dict(self.metrics["requests"]),
            "status_code_distribution": dict(self.metrics["status_codes"]),
            "slowest_endpoints": [
                {"endpoint": ep, **stats} for ep, stats in slowest
            ],
            "error_prone_endpoints": [
                {"endpoint": ep, "count": v["count"], "errors": v["errors"]}
                for ep, v in error_prone
            ],
        }

    def get_health_score(self) -> dict:
        """Calculate a health score (0-100) based on metrics."""
        metrics = self.get_metrics()

        # Factors
        error_rate = metrics["error_rate_percent"]
        uptime = metrics["uptime_seconds"]

        # Score calculation
        score = 100

        # Penalize errors
        if error_rate > 10:
            score -= 30
        elif error_rate > 5:
            score -= 20
        elif error_rate > 1:
            score -= 10

        # Bonus for uptime
        if uptime > 86400:  # > 24 hours
            score += 5
        elif uptime > 3600:  # > 1 hour
            score += 2

        # Check response times
        all_times = []
        for times in self.metrics["response_times"].values():
            all_times.extend(times)

        if all_times:
            avg_time = sum(all_times) / len(all_times)
            if avg_time > 1000:  # > 1 second
                score -= 20
            elif avg_time > 500:
                score -= 10
            elif avg_time < 100:
                score += 5

        score = max(0, min(100, score))

        if score >= 90:
            status = "excellent"
        elif score >= 75:
            status = "good"
        elif score >= 50:
            status = "fair"
        else:
            status = "poor"

        return {
            "score": score,
            "status": status,
            "factors": {
                "error_rate": error_rate,
                "uptime_hours": round(uptime / 3600, 1),
                "avg_response_ms": round(sum(all_times) / max(len(all_times), 1), 1),
            },
        }


# Global APM instance
apm = APMMiddleware(None)  # Will be attached to app
