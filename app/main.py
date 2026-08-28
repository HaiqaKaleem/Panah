from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.models import (
    Capture, Media, Observation, Project, Site,
    Material, ValidationRun, ValidationResult, Review,
)
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

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Panagah API",
    version="1.0.0",
    description=(
        "Humanitarian Shelter Assessment & Design Platform — "
        "from field data capture through constraint-driven design generation, "
        "structural analysis, Sphere Handbook compliance, and engineer review."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS (allows frontend on different origin during dev & production) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core CRUD Routers ---
app.include_router(projects_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
app.include_router(observations_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")

# --- Requirements Screen ---
app.include_router(site_profiles_router, prefix="/api/v1")
app.include_router(design_specifications_router, prefix="/api/v1")
app.include_router(constraint_sets_router, prefix="/api/v1")

# --- Materials Screen ---
app.include_router(materials_router, prefix="/api/v1")
app.include_router(materials_summary_router, prefix="/api/v1")
app.include_router(material_catalog_router, prefix="/api/v1")

# --- Generation & Design ---
app.include_router(design_candidates_router, prefix="/api/v1")
app.include_router(design_versions_router, prefix="/api/v1")
app.include_router(generated_designs_router, prefix="/api/v1")
app.include_router(generated_validation_router, prefix="/api/v1")
app.include_router(comparison_router, prefix="/api/v1")

# --- Validation, Standards & Compliance ---
app.include_router(validation_router, prefix="/api/v1")
app.include_router(standards_router, prefix="/api/v1")
app.include_router(load_combinations_router, prefix="/api/v1")

# --- Review Workflow ---
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")

# --- 3D Geometry ---
app.include_router(geometry_router, prefix="/api/v1")

# --- Export & Reporting ---
app.include_router(bom_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")

# --- Dashboard & Analytics ---
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(project_history_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")

# --- Deterministic Validation Engine (YAML Rules) ---
app.include_router(design_validation_router, prefix="/api/v1")

# --- Engineering Calculations ---
app.include_router(engineering_router, prefix="/api/v1")

# --- Platform Services (jobs, webhooks, API keys, geo-climate, export) ---
app.include_router(platform_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "version": "0.7.0"}


@app.get("/", tags=["System"])
def root():
    return {
        "name": "Panagah API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "routers": 28,
        "description": "Humanitarian Shelter Assessment & Design Platform",
    }
