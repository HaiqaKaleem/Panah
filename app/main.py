from fastapi import FastAPI
from app.core.database import Base, engine
from app.models import Capture, Media, Observation, Project, Site
from app.api.projects import router as projects_router
from app.api.sites import router as sites_router
from app.api.media import router as media_router
from app.api.observations import router as observations_router
from app.api.analysis import router as analysis_router
from app.api.site_profiles import router as site_profiles_router
from app.api.design_specifications import router as design_specifications_router
from app.api.design_candidates import router as design_candidates_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Panagah API", version="0.4.0")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(sites_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")
app.include_router(observations_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(site_profiles_router, prefix="/api/v1")
app.include_router(design_specifications_router, prefix="/api/v1")
app.include_router(design_candidates_router, prefix="/api/v1")

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}
