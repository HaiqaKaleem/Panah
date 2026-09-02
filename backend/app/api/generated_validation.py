import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.compliance.service import ComplianceStatus, evaluate_compliance
from app.constraints.schemas import ConstraintSet
from app.core.database import get_db
from app.models.generated_design import GeneratedDesign
from app.models.constraint_set import ConstraintSetRecord
from app.rules import evaluate_rules
from app.schemas.design_version import CanonicalDesignVersion
from app.services.audit import log_event
from app.structural.analysis import analyze_structure

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Generated Design Validation"],
)


@router.post(
    "/generated-designs/{design_id}/validate",
    status_code=201,
)
def validate_generated_design(
    project_id: int,
    site_id: int,
    design_id: int,
    db: Session = Depends(get_db),
):
    """
    Run the full validation pipeline on a generated design:
    1. Structural analysis (simplified prescreen)
    2. Sphere Handbook rule evaluation
    3. Compliance mapping

    Returns the combined analysis, rules, and compliance report.
    """
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    # Load the constraint set used for generation
    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    if cs_record is None:
        raise HTTPException(status_code=404, detail="Original constraint set not found")

    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json)

    # Parse the design version from the stored JSON
    design_data = json.loads(record.design_json)
    design_version = CanonicalDesignVersion.model_validate(design_data)

    # Run structural analysis
    analysis = analyze_structure(
        constraints,
        members=design_version.members,
        design_height_m=design_version.height_m,
    )

    # Run Sphere rule evaluation
    rules_evaluation = evaluate_rules(constraints, analysis)

    # Map to compliance report
    compliance = evaluate_compliance(
        analysis=None,  # compliance uses the analysis data via rule results
        rule_results=[r.to_dict() for r in rules_evaluation.results],
        standard="Sphere Handbook V24.1",
    )

    # Update the record with analysis + rules
    record.analysis_json = json.dumps(analysis.to_dict())
    record.rules_json = json.dumps(rules_evaluation.to_dict())
    db.commit()

    log_event(
        db,
        project_id=project_id,
        action="generated_design_validated",
        object_type="generated_design",
        object_id=str(design_id),
        details={
            "compliance_status": compliance.status.value,
            "rule_count": len(rules_evaluation.results),
            "integrity_score": analysis.overall_integrity_score,
        },
    )
    db.commit()

    return {
        "design_id": design_id,
        "analysis": analysis.to_dict(),
        "rules": rules_evaluation.to_dict(),
        "compliance": compliance.to_dict(),
    }
