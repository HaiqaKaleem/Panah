"""
Design Validation API — deterministic YAML rule engine.

Provides an endpoint that runs the new rule-based validator
alongside the existing structural analysis pipeline.
"""
from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.generated_design import GeneratedDesign
from app.models.constraint_set import ConstraintSetRecord
from app.constraints.schemas import ConstraintSet
from app.schemas.design_version import CanonicalDesignVersion
from app.structural.analysis import analyze_structure
from app.validator import validate_design, build_context, list_rules, reload_rules
from app.validator.result import ValidationReport
from app.services.audit import log_event

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Design Validation (YAML Rules)"],
)


@router.post(
    "/generated-designs/{design_id}/validate-rules",
    status_code=201,
)
def validate_with_yaml_rules(
    project_id: int,
    site_id: int,
    design_id: int,
    rule_ids: Optional[List[str]] = Query(default=None, description="Subset of rule IDs to run"),
    db: Session = Depends(get_db),
):
    """
    Run the deterministic YAML rule engine on a generated design.

    This endpoint runs the rule-based validator independently of the
    existing compliance pipeline, providing a pure-engineering check
    against Sphere Handbook and structural rules.
    """
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    if cs_record is None:
        raise HTTPException(status_code=404, detail="Original constraint set not found")

    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json)
    design_data = json.loads(record.design_json)
    design = CanonicalDesignVersion.model_validate(design_data)

    # Run structural analysis for context enrichment
    analysis = analyze_structure(
        constraints,
        members=design.members,
        design_height_m=design.height_m,
    )

    # Build validation context and run rules
    context = build_context(design, constraints, analysis)
    report = validate_design(context, rule_ids=rule_ids)

    # Audit
    log_event(
        db,
        project_id=project_id,
        action="yaml_rule_validation",
        object_type="generated_design",
        object_id=str(design_id),
        details={
            "overall_status": report.overall_status,
            "total_rules": report.total,
            "passed": report.passed_count,
            "failed": report.failed_count,
            "skipped": report.skipped_count,
            "errors": report.error_count,
            "blocking": report.blocking_count,
        },
    )
    db.commit()

    return {
        "design_id": design_id,
        "report": report.to_dict(),
    }


@router.get(
    "/design-validation/rules",
    response_model=List[str],
)
def get_validation_rules():
    """List all available deterministic validation rule IDs."""
    return list_rules()


@router.post(
    "/design-validation/reload-rules",
)
def reload_validation_rules():
    """Force reload YAML rule definitions from disk (for development)."""
    reload_rules()
    return {"reloaded": True, "rule_count": len(list_rules())}
