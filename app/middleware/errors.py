"""Global exception handlers for consistent error responses."""

import logging
import traceback
import uuid
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger("panagah.errors")


def register_exception_handlers(app: FastAPI):
    """Register all exception handlers on the app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """422 Validation Error — structured response."""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": errors,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_error_handler(request: Request, exc: ValidationError):
        """422 Pydantic Validation Error."""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": "schema_error",
                "message": "Data validation failed",
                "details": errors,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """404 Not Found."""
        # Extract detail from Starlette's HTTPException if present
        detail = getattr(exc, 'detail', f"Resource not found: {request.url.path}")
        return JSONResponse(
            status_code=404,
            content={
                "detail": detail,
                "error": "not_found",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        """500 Internal Server Error — never leak stack traces."""
        error_id = str(uuid.uuid4())[:8]
        logger.error(
            f"Internal error [{error_id}]: {exc}",
            extra={"error_id": error_id, "path": str(request.url.path)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions."""
        error_id = str(uuid.uuid4())[:8]
        logger.error(
            f"Unhandled exception [{error_id}]: {exc}",
            extra={
                "error_id": error_id,
                "path": str(request.url.path),
                "traceback": traceback.format_exc()[:500],
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "server_error",
                "message": "An unexpected error occurred",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
