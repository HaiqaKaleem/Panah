import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.sites import get_site_or_404
from app.constraints.schemas import ConstraintSet
from app.core.database import get_db
from app.generator.converter import candidate_to_design_version
from app.generator.service import LocalGenerationService
from app.models.constraint_set import ConstraintSetRecord
from app.models.generated_design import GeneratedDesign
from app.rules import evaluate_rules
from app.schemas.constraint_set import (
    ConstraintSetResponse,
    GenerateRequest,
    GeneratedDesignDetail,
    GeneratedDesignSummary,
    constraint_set_to_response,
    generated_design_to_detail,
    generated_design_to_summary,
)
from app.structural.analysis import analyze_structure

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Constraint Sets & Generation"],
)


def get_constraint_set_or_404(
    site_id: int,
    constraint_set_id: int,
    db: Session,
) -> ConstraintSetRecord:
    record = db.get(ConstraintSetRecord, constraint_set_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constraint set not found",
        )
    return record


@router.post(
    "/constraint-sets",
    response_model=ConstraintSetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_constraint_set(
    project_id: int,
    site_id: int,
    payload: ConstraintSet,
    db: Session = Depends(get_db),
):
    get_site_or_404(project_id, site_id, db)

    record = ConstraintSetRecord(
        site_id=site_id,
        version=payload.version,
        constraint_json=payload.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return constraint_set_to_response(record)


@router.get(
    "/constraint-sets",
    response_model=list[ConstraintSetResponse],
)
def list_constraint_sets(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    get_site_or_404(project_id, site_id, db)

    statement = (
        select(ConstraintSetRecord)
        .where(ConstraintSetRecord.site_id == site_id)
        .order_by(ConstraintSetRecord.created_at.desc())
    )
    records = db.scalars(statement).all()

    return [constraint_set_to_response(record) for record in records]


@router.get(
    "/constraint-sets/{constraint_set_id}",
    response_model=ConstraintSetResponse,
)
def get_constraint_set(
    project_id: int,
    site_id: int,
    constraint_set_id: int,
    db: Session = Depends(get_db),
):
    get_site_or_404(project_id, site_id, db)
    record = get_constraint_set_or_404(site_id, constraint_set_id, db)
    return constraint_set_to_response(record)


@router.post(
    "/constraint-sets/{constraint_set_id}/generate",
    response_model=list[GeneratedDesignSummary],
    status_code=status.HTTP_201_CREATED,
)
def generate_designs(
    project_id: int,
    site_id: int,
    constraint_set_id: int,
    payload: GenerateRequest = GenerateRequest(),
    db: Session = Depends(get_db),
):
    """
    Run the full local pipeline for one ConstraintSet:

    ConstraintSet -> LocalGenerationService -> CanonicalDesignVersion
        -> structural analysis -> Sphere rule evaluation -> persisted result

    Returns a summary per candidate so the Build screen can present a
    candidate picker (integrity score, compliance, blocking rule count)
    before the person opens the full detail view.
    """
    get_site_or_404(project_id, site_id, db)
    record = get_constraint_set_or_404(site_id, constraint_set_id, db)
    constraints = ConstraintSet.model_validate_json(record.constraint_json)

    try:
        candidates = LocalGenerationService().generate_candidates(
            constraints,
            count=payload.count,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    created: list[GeneratedDesign] = []

    for candidate in candidates:
        design_version = candidate_to_design_version(
            candidate,
            version=f"DV-{candidate.candidate_id}",
        )
        analysis = analyze_structure(
            constraints,
            members=design_version.members,
            design_height_m=design_version.height_m,
        )
        evaluation = evaluate_rules(constraints, analysis)

        design_record = GeneratedDesign(
            site_id=site_id,
            constraint_set_id=constraint_set_id,
            candidate_id=candidate.candidate_id,
            version=design_version.version,
            status="generated",
            design_json=design_version.model_dump_json(),
            analysis_json=json.dumps(analysis.to_dict()),
            rules_json=json.dumps(evaluation.to_dict()),
        )
        db.add(design_record)
        created.append(design_record)

    db.commit()
    for design_record in created:
        db.refresh(design_record)

    return [generated_design_to_summary(record) for record in created]


@router.get(
    "/generated-designs",
    response_model=list[GeneratedDesignSummary],
)
def list_generated_designs(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    get_site_or_404(project_id, site_id, db)

    statement = (
        select(GeneratedDesign)
        .where(GeneratedDesign.site_id == site_id)
        .order_by(GeneratedDesign.created_at.desc())
    )
    records = db.scalars(statement).all()

    return [generated_design_to_summary(record) for record in records]


@router.get(
    "/generated-designs/{design_id}",
    response_model=GeneratedDesignDetail,
)
def get_generated_design(
    project_id: int,
    site_id: int,
    design_id: int,
    db: Session = Depends(get_db),
):
    get_site_or_404(project_id, site_id, db)

    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated design not found",
        )

    return generated_design_to_detail(record)


@router.patch(
    "/generated-designs/{design_id}/status",
    response_model=GeneratedDesignSummary,
)
def update_generated_design_status(
    project_id: int,
    site_id: int,
    design_id: int,
    status_value: str,
    db: Session = Depends(get_db),
):
    get_site_or_404(project_id, site_id, db)

    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated design not found",
        )

    if status_value not in {"selected", "rejected", "generated"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status must be selected, rejected, or generated",
        )

    record.status = status_value
    db.commit()
    db.refresh(record)

    return generated_design_to_summary(record)
