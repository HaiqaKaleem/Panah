"""Project History API — enriched project listing with counts for the History screen."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.models.site import Site
from app.models.material import Material
from app.models.design_candidate import DesignCandidate
from app.models.generated_design import GeneratedDesign
from app.models.design_version import DesignVersion

router = APIRouter(prefix="/projects-history", tags=["Project History"])


@router.get("")
def list_projects_with_counts(db: Session = Depends(get_db)):
    """
    List all projects enriched with counts for the Project History screen.
    Returns site count, material count, candidate count, and design count per project.
    """
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    result = []

    for project in projects:
        site_ids = [
            s.id for s in
            db.query(Site.id).filter(Site.project_id == project.id).all()
        ]

        site_count = len(site_ids)
        material_count = 0
        candidate_count = 0
        generated_count = 0
        design_version_count = 0

        if site_ids:
            material_count = (
                db.query(func.count(Material.id))
                .filter(Material.project_id == project.id)
                .scalar() or 0
            )
            candidate_count = (
                db.query(func.count(DesignCandidate.id))
                .filter(DesignCandidate.site_id.in_(site_ids))
                .scalar() or 0
            )
            generated_count = (
                db.query(func.count(GeneratedDesign.id))
                .filter(GeneratedDesign.site_id.in_(site_ids))
                .scalar() or 0
            )
            design_version_count = (
                db.query(func.count(DesignVersion.id))
                .filter(DesignVersion.site_id.in_(site_ids))
                .scalar() or 0
            )

        result.append({
            "id": project.id,
            "name": project.name,
            "location": project.location,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "site_count": site_count,
            "material_count": material_count,
            "candidate_count": candidate_count,
            "generated_design_count": generated_count,
            "design_version_count": design_version_count,
            "total_activity": site_count + candidate_count + generated_count + design_version_count,
        })

    return {
        "count": len(result),
        "projects": result,
    }



