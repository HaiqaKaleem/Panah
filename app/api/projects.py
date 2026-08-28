from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    project = Project(
        name=payload.name,
        location=payload.location,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def list_projects(
    db: Session = Depends(get_db),
):
    statement = select(Project).order_by(Project.created_at.desc())
    return list(db.scalars(statement).all())


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    # Empty PATCH is a harmless no-op.
    for field, value in updates.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    db.delete(project)
    db.commit()


@router.get("/{project_id}/stats")
def get_project_stats(project_id: int, db: Session = Depends(get_db)): 
    """Return project-level statistics for the dashboard."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.models.site import Site
    from app.models.material import Material
    from app.models.design_candidate import DesignCandidate
    from app.models.design_version import DesignVersion
    from app.models.generated_design import GeneratedDesign

    site_count = db.query(Site).filter(Site.project_id == project_id).count()
    material_count = db.query(Material).filter(Material.project_id == project_id).count()

    site_ids = [s.id for s in db.query(Site.id).filter(Site.project_id == project_id).all()]

    candidate_count = 0
    design_version_count = 0
    generated_design_count = 0
    if site_ids:
        candidate_count = db.query(DesignCandidate).filter(DesignCandidate.site_id.in_(site_ids)).count()
        design_version_count = db.query(DesignVersion).filter(DesignVersion.site_id.in_(site_ids)).count()
        generated_design_count = db.query(GeneratedDesign).filter(GeneratedDesign.site_id.in_(site_ids)).count()

    return {
        "project_id": project_id,
        "name": project.name,
        "site_count": site_count,
        "material_count": material_count,
        "candidate_count": candidate_count,
        "design_version_count": design_version_count,
        "generated_design_count": generated_design_count,
    }
