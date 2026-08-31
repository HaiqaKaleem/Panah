from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.capture import Capture
from app.models.project import Project
from app.models.site import Site
from app.schemas.site import (
    CaptureCreate,
    CaptureResponse,
    SiteCreate,
    SiteResponse,
    SiteUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/sites", tags=["Sites"])


def get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def get_site_or_404(project_id: int, site_id: int, db: Session) -> Site:
    site = db.get(Site, site_id)

    if site is None or site.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    return site


@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_site(
    project_id: int,
    payload: SiteCreate,
    db: Session = Depends(get_db),
):
    get_project_or_404(project_id, db)

    site = Site(
        project_id=project_id,
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return site


@router.get(
    "",
    response_model=list[SiteResponse],
)
def list_sites(
    project_id: int,
    db: Session = Depends(get_db),
):
    get_project_or_404(project_id, db)

    statement = (
        select(Site)
        .where(Site.project_id == project_id)
        .order_by(Site.created_at.desc())
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
)
def get_site(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    return get_site_or_404(project_id, site_id, db)


@router.patch(
    "/{site_id}",
    response_model=SiteResponse,
)
def update_site(
    project_id: int,
    site_id: int,
    payload: SiteUpdate,
    db: Session = Depends(get_db),
):
    site = get_site_or_404(project_id, site_id, db)

    updates = payload.model_dump(exclude_unset=True)

    # Explicitly prevent clearing the required name.
    if "name" in updates and updates["name"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="name cannot be null",
        )

    for field, value in updates.items():
        setattr(site, field, value)

    db.commit()
    db.refresh(site)

    return site


@router.post(
    "/{site_id}/captures",
    response_model=CaptureResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_capture(
    project_id: int,
    site_id: int,
    payload: CaptureCreate,
    db: Session = Depends(get_db),
):
    site = get_site_or_404(project_id, site_id, db)

    capture = Capture(
        site_id=site.id,
        captured_at=payload.captured_at,
        latitude=payload.latitude,
        longitude=payload.longitude,
        notes=payload.notes,
    )

    db.add(capture)

    # A site now has at least one field capture.
    site.status = "capture_uploaded"

    db.commit()
    db.refresh(capture)

    return capture


@router.get(
    "/{site_id}/captures",
    response_model=list[CaptureResponse],
)
def list_captures(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    site = get_site_or_404(project_id, site_id, db)

    statement = (
        select(Capture)
        .where(Capture.site_id == site.id)
        .order_by(Capture.captured_at.desc())
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{site_id}/captures/{capture_id}",
    response_model=CaptureResponse,
)
def get_capture(
    project_id: int,
    site_id: int,
    capture_id: int,
    db: Session = Depends(get_db),
):
    site = get_site_or_404(project_id, site_id, db)

    capture = db.get(Capture, capture_id)

    if capture is None or capture.site_id != site.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capture not found",
        )

    return capture
