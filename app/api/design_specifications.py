import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.design_specification import DesignSpecification
from app.models.site import Site
from app.models.site_profile import SiteProfile
from app.schemas.design_specification import (
    DesignSpecificationResponse,
    DesignSpecificationUpdate,
)

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/design-specification",
    tags=["Design Specification"],
)


def get_site(project_id: int, site_id: int, db: Session) -> Site:
    site = db.get(Site, site_id)

    if site is None or site.project_id != project_id:
        raise HTTPException(
            status_code=404,
            detail="Site not found",
        )

    return site


def get_specification(
    project_id: int,
    site_id: int,
    db: Session,
) -> DesignSpecification:
    get_site(project_id, site_id, db)

    specification = (
        db.query(DesignSpecification)
        .filter(DesignSpecification.site_id == site_id)
        .first()
    )

    if specification is None:
        raise HTTPException(
            status_code=404,
            detail="Design specification not found",
        )

    return specification


@router.get("", response_model=DesignSpecificationResponse)
def get_design_specification(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    return get_specification(project_id, site_id, db)


@router.put("", response_model=DesignSpecificationResponse)
def save_design_specification(
    project_id: int,
    site_id: int,
    payload: DesignSpecificationUpdate,
    db: Session = Depends(get_db),
):
    get_site(project_id, site_id, db)

    # The specification is a design request, not a safety verdict.
    data = payload.model_dump()

    specification = (
        db.query(DesignSpecification)
        .filter(DesignSpecification.site_id == site_id)
        .first()
    )

    if specification is None:
        specification = DesignSpecification(
            site_id=site_id,
            status="draft",
            specification_json=json.dumps(data),
        )
        db.add(specification)
    else:
        specification.specification_json = json.dumps(data)
        # Editing a specification means it needs to be treated as draft again.
        specification.status = "draft"

    db.commit()
    db.refresh(specification)

    return specification


@router.post("/ready", response_model=DesignSpecificationResponse)
def mark_design_specification_ready(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    specification = get_specification(project_id, site_id, db)

    data = json.loads(specification.specification_json)

    if not data.get("family_size"):
        raise HTTPException(
            status_code=422,
            detail="Family size is required",
        )

    # If the coordinator specified a footprint, it must be positive
    # (already enforced by the schema, but this protects stored JSON too).
    footprint = data.get("maximum_footprint_m2")
    if footprint is not None and footprint <= 0:
        raise HTTPException(
            status_code=422,
            detail="Maximum footprint must be positive",
        )

    specification.status = "ready"
    db.commit()
    db.refresh(specification)

    return specification
