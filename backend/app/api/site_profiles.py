import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.site import Site
from app.models.site_profile import SiteProfile
from app.schemas.site_profile import SiteProfileResponse, SiteProfileUpdate

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/profile",
    tags=["Site Profile"],
)


def get_site(project_id: int, site_id: int, db: Session) -> Site:
    site = db.get(Site, site_id)
    if site is None or site.project_id != project_id:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


def get_profile(project_id: int, site_id: int, db: Session) -> SiteProfile:
    get_site(project_id, site_id, db)

    profile = (
        db.query(SiteProfile)
        .filter(SiteProfile.site_id == site_id)
        .first()
    )

    if profile is None:
        raise HTTPException(status_code=404, detail="Site profile not found")

    return profile


@router.get("", response_model=SiteProfileResponse)
def get_site_profile(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    return get_profile(project_id, site_id, db)


@router.put("", response_model=SiteProfileResponse)
def save_site_profile(
    project_id: int,
    site_id: int,
    payload: SiteProfileUpdate,
    db: Session = Depends(get_db),
):
    get_site(project_id, site_id, db)

    profile = (
        db.query(SiteProfile)
        .filter(SiteProfile.site_id == site_id)
        .first()
    )

    if profile is None:
        profile = SiteProfile(
            site_id=site_id,
            status="draft",
            profile_json=json.dumps(payload.model_dump()),
        )
        db.add(profile)
    else:
        profile.profile_json = json.dumps(payload.model_dump())

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/ready", response_model=SiteProfileResponse)
def mark_profile_ready(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    profile = get_profile(project_id, site_id, db)

    data = json.loads(profile.profile_json)

    # A profile cannot be marked ready with no actual site information.
    has_content = any(bool(value) for value in data.values())

    if not has_content:
        raise HTTPException(
            status_code=422,
            detail="Site profile contains no usable site information",
        )

    profile.status = "ready"
    db.commit()
    db.refresh(profile)
    return profile
