import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.site_profiles import get_profile
from app.api.design_specifications import get_specification
from app.core.database import get_db
from app.design.base import GenerationInput
from app.design.factory import get_design_generator
from app.models.design_candidate import DesignCandidate
from app.schemas.design_candidate import (
    DesignCandidatePayload,
    DesignCandidateResponse,
)
from app.services.audit import log_event

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/design-candidates",
    tags=["Design Candidates"],
)


@router.post(
    "/generate",
    response_model=DesignCandidateResponse,
    status_code=201,
)
def generate_design_candidate(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    site_profile = get_profile(project_id, site_id, db)
    specification = get_specification(project_id, site_id, db)

    if site_profile.status != "ready":
        raise HTTPException(
            status_code=422,
            detail="Site profile must be ready before generation",
        )

    if specification.status != "ready":
        raise HTTPException(
            status_code=422,
            detail="Design specification must be ready before generation",
        )

    site_profile_data = json.loads(site_profile.profile_json)
    specification_data = json.loads(specification.specification_json)

    generator = get_design_generator()

    try:
        raw_candidate = generator.generate(
            GenerationInput(
                site_profile=site_profile_data,
                design_specification=specification_data,
            )
        )

        # Validate the generator's output against our contract before storing it.
        validated = DesignCandidatePayload.model_validate(raw_candidate)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Design generator returned invalid output: {exc}",
        )

    input_snapshot = {
        "site_profile": site_profile_data,
        "design_specification": specification_data,
    }

    candidate = DesignCandidate(
        site_id=site_id,
        design_specification_id=specification.id,
        status="generated",
        generator_name=generator.name,
        generator_version=generator.version,
        candidate_json=validated.model_dump_json(),
        input_snapshot_json=json.dumps(input_snapshot),
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    log_event(
        db,
        project_id=project_id,
        action="design_candidate_generated",
        object_type="design_candidate",
        object_id=str(candidate.id),
        details={
            "site_id": site_id,
            "generator": generator.name,
            "specification_id": specification.id,
        },
    )
    db.commit()

    return candidate


@router.get("", response_model=list[DesignCandidateResponse])
def list_design_candidates(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    # Validate site through the existing profile/specification ownership checks.
    get_profile(project_id, site_id, db)

    candidates = (
        db.query(DesignCandidate)
        .filter(DesignCandidate.site_id == site_id)
        .order_by(DesignCandidate.created_at.desc())
        .all()
    )

    return candidates


@router.get("/{candidate_id}", response_model=DesignCandidateResponse)
def get_design_candidate(
    project_id: int,
    site_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
):
    get_profile(project_id, site_id, db)

    candidate = db.get(DesignCandidate, candidate_id)

    if candidate is None or candidate.site_id != site_id:
        raise HTTPException(
            status_code=404,
            detail="Design candidate not found",
        )

    return candidate


@router.patch("/{candidate_id}/status", response_model=DesignCandidateResponse)
def update_design_candidate_status(
    project_id: int,
    site_id: int,
    candidate_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    get_profile(project_id, site_id, db)

    if status not in {"selected", "rejected"}:
        raise HTTPException(
            status_code=422,
            detail="Status must be selected or rejected",
        )

    candidate = db.get(DesignCandidate, candidate_id)

    if candidate is None or candidate.site_id != site_id:
        raise HTTPException(
            status_code=404,
            detail="Design candidate not found",
        )

    candidate.status = status
    db.commit()
    db.refresh(candidate)

    return candidate
