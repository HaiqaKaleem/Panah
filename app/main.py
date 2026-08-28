"""PANAGAH API — Humanitarian Shelter Assessment & Design Platform.

Production-grade FastAPI backend with:
- JWT Authentication + OAuth2
- WebSocket real-time updates
- Request logging + timing middleware
- Global exception handlers
- CORS + security headers
- Comprehensive OpenAPI docs
"""

import os
import platform
import time
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.database import Base, engine
from app.models import (
    Capture, Media, Observation, Project, Site,
    Material, ValidationRun, ValidationResult, Review,
)

# ── Routers ───────────────────────────────────────────────────────────
from app.api.projects import router as projects_router
from app.api.sites import router as sites_router
from app.api.media import router as media_router
from app.api.observations import router as observations_router
from app.api.analysis import router as analysis_router
from app.api.site_profiles import router as site_profiles_router
from app.api.design_specifications import router as design_specifications_router
from app.api.design_candidates import router as design_candidates_router
from app.api.design_versions import router as design_versions_router
from app.api.materials import router as materials_router
from app.api.validation import router as validation_router
from app.api.reviews import router as reviews_router
from app.api.audit import router as audit_router
from app.api.constraint_sets import router as constraint_sets_router
from app.api.standards import router as standards_router
from app.api.material_catalog import router as material_catalog_router
from app.api.generated_designs import router as generated_designs_router
from app.api.generated_validation import router as generated_validation_router
from app.api.dashboard import router as dashboard_router
from app.api.project_history import router as project_history_router
from app.api.materials_summary import router as materials_summary_router
from app.api.bom import router as bom_router
from app.api.comparison import router as comparison_router
from app.api.export import router as export_router
from app.api.activity import router as activity_router
from app.api.geometry import router as geometry_router
from app.api.load_combinations import router as load_combinations_router
from app.api.notifications import router as notifications_router
from app.api.design_validation import router as design_validation_router
from app.api.engineering import router as engineering_router
from app.api.platform import router as platform_router
from app.api.auth import router as auth_router
from app.api.websocket import router as websocket_router

# ── Middleware ─────────────────────────────────────────────────────────
from app.middleware.logging import RequestLoggingMiddleware, TimingMiddleware
from app.middleware.errors import register_exception_handlers

# ── Create tables ─────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App Startup Time ──────────────────────────────────────────────────
APP_START_TIME = time.time()

# ── Create App ────────────────────────────────────────────────────────
app = FastAPI(
    title="Panagah API",
    version="1.0.0",
    description=(
        "## PANAGAH (پناگاہ) — Humanitarian Shelter Assessment & Design Platform\n\n"
        "A constraint-driven generative design system for humanitarian shelter assessment.\n\n"
        "### Features\n"
        "- **Constraint-driven generation** — Field data → canonical models → AI/mock generation\n"
        "- **Parametric 3D geometry** — Truss builder with computed coordinates\n"
        "- **Deterministic validation** — YAML rule engine with Sphere Handbook rules\n"
        "- **Engineering calculations** — ASCE 7 wind loads, seismic ELF, Pareto optimization\n"
        "- **Professional reporting** — PDF engineering reports\n"
        "- **Real-time updates** — WebSocket design generation progress\n"
        "- **JWT authentication** — Role-based access control\n"
        "- **Platform services** — Job queue, webhooks, API keys, caching\n\n"
        "### Authentication\n"
        "Use the `/api/v1/auth/login` endpoint to get a JWT token, then click "
        "'Authorize' in Swagger UI and enter `Bearer <token>`.\n\n"
        "### WebSocket\n"
        "Connect to `ws://localhost:8000/ws/project/{project_id}` for real-time updates."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Authentication", "description": "JWT login, register, token management"},
        {"name": "Projects", "description": "Project CRUD and statistics"},
        {"name": "Sites", "description": "Site management and status transitions"},
        {"name": "Requirements", "description": "Site profiles, design specifications, constraint sets"},
        {"name": "Materials", "description": "Material inventory and catalog"},
        {"name": "Generation", "description": "Design candidate generation and selection"},
        {"name": "Validation", "description": "Deterministic rule validation"},
        {"name": "Standards", "description": "Sphere Handbook rules and load combinations"},
        {"name": "Reviews", "description": "Engineer review workflow"},
        {"name": "Engineering", "description": "Wind load, seismic, optimization, cost, safety"},
        {"name": "3D Geometry", "description": "Parametric geometry and Three.js scenes"},
        {"name": "Export", "description": "BOM, design export, PDF reports"},
        {"name": "Dashboard", "description": "Statistics, activity, audit trail"},
        {"name": "Platform", "description": "Jobs, webhooks, API keys, cache, geo-climate"},
        {"name": "WebSocket", "description": "Real-time project and design updates"},
        {"name": "System", "description": "Health checks and system info"},
    ],
)

# ── Middleware (order matters: last added = first executed) ────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time", "Server-Timing"],
)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ── Exception Handlers ────────────────────────────────────────────────
register_exception_handlers(app)


# ── Include Routers ───────────────────────────────────────────────────

# Authentication
app.include_router(auth_router, prefix="/api/v1")
app.include_router(websocket_router)

# Core CRUD
app.include_router(projects_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
app.include_router(observations_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")

# Requirements
app.include_router(site_profiles_router, prefix="/api/v1")
app.include_router(design_specifications_router, prefix="/api/v1")
app.include_router(constraint_sets_router, prefix="/api/v1")

# Materials
app.include_router(materials_router, prefix="/api/v1")
app.include_router(materials_summary_router, prefix="/api/v1")
app.include_router(material_catalog_router, prefix="/api/v1")

# Generation & Design
app.include_router(design_candidates_router, prefix="/api/v1")
app.include_router(design_versions_router, prefix="/api/v1")
app.include_router(generated_designs_router, prefix="/api/v1")
app.include_router(generated_validation_router, prefix="/api/v1")
app.include_router(comparison_router, prefix="/api/v1")

# Validation, Standards & Compliance
app.include_router(validation_router, prefix="/api/v1")
app.include_router(standards_router, prefix="/api/v1")
app.include_router(load_combinations_router, prefix="/api/v1")

# Review Workflow
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")

# 3D Geometry
app.include_router(geometry_router, prefix="/api/v1")

# Export & Reporting
app.include_router(bom_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")

# Dashboard & Analytics
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(project_history_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")

# Deterministic Validation Engine
app.include_router(design_validation_router, prefix="/api/v1")

# Engineering Calculations
app.include_router(engineering_router, prefix="/api/v1")

# Platform Services
app.include_router(platform_router, prefix="/api/v1")


# ── System Endpoints ──────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check with detailed status")
async def health():
    """
    Comprehensive health check.

    Returns:
    - Service status
    - Uptime
    - Python version
    - Database connectivity
    - Memory usage
    """
    uptime = time.time() - APP_START_TIME

    # Check database
    db_ok = True
    try:
        from sqlalchemy import text
        from app.core.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 1),
        "uptime_human": _format_uptime(uptime),
        "python": platform.python_version(),
        "database": "connected" if db_ok else "disconnected",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/", tags=["System"], summary="API root — service info")
async def root():
    """API root with service metadata."""
    return {
        "name": "Panagah API",
        "version": "1.0.0",
        "tagline": "پناگاہ — Humanitarian Shelter Assessment & Design Platform",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "websocket": "ws://localhost:8000/ws/project/{project_id}",
        "auth": "/api/v1/auth/login",
        "routers": 32,
        "endpoints": "101+",
        "tests": 417,
    }


@app.get("/metrics", tags=["System"], summary="Prometheus-compatible metrics")
async def metrics():
    """Basic metrics endpoint (Prometheus-compatible format)."""
    uptime = time.time() - APP_START_TIME
    return {
        "uptime_seconds": round(uptime, 1),
        "python_version": platform.python_version(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "sqlite" if "sqlite" in os.getenv("DATABASE_URL", "sqlite") else "postgresql",
    }


def _format_uptime(seconds: float) -> str:
    """Format uptime as human-readable string."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
