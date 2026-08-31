"""Dashboard API — global and per-project metrics for the Dashboard screen."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.models.site import Site
from app.models.material import Material
from app.models.design_candidate import DesignCandidate
from app.models.design_version import DesignVersion
from app.models.generated_design import GeneratedDesign
from app.models.audit import AuditEvent
from app.models.review import Review
from app.models.validation import ValidationRun

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Global dashboard statistics for the landing screen."""
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_sites = db.query(func.count(Site.id)).scalar() or 0
    total_materials = db.query(func.count(Material.id)).scalar() or 0
    total_candidates = db.query(func.count(DesignCandidate.id)).scalar() or 0
    total_generated = db.query(func.count(GeneratedDesign.id)).scalar() or 0
    total_design_versions = db.query(func.count(DesignVersion.id)).scalar() or 0
    total_validation_runs = db.query(func.count(ValidationRun.id)).scalar() or 0
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    total_audit_events = db.query(func.count(AuditEvent.id)).scalar() or 0

    # Active projects (those with at least one site)
    active_projects = (
        db.query(func.count(func.distinct(Site.project_id)))
        .scalar() or 0
    )

    # Recent activity
    recent_events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_sites": total_sites,
        "total_materials": total_materials,
        "total_candidates": total_candidates,
        "total_generated_designs": total_generated,
        "total_design_versions": total_design_versions,
        "total_validation_runs": total_validation_runs,
        "total_reviews": total_reviews,
        "total_audit_events": total_audit_events,
        "recent_activity": [
            {
                "id": e.id,
                "action": e.action,
                "object_type": e.object_type,
                "object_id": e.object_id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent_events
        ],
    }
