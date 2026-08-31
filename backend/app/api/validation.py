from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.service import analyze_design
from app.compliance.service import ComplianceStatus, evaluate_compliance
from app.core.database import get_db
from app.models.design_version import DesignVersion
from app.models.validation import ValidationResult, ValidationRun
from app.schemas.design_version import CanonicalDesignVersion
from app.schemas.validation import (
    ValidationReportResponse,
    ValidationResultResponse,
    ValidationRunResponse,
)
from app.services.audit import log_event

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/design-versions",
    tags=["Validation"],
)


def get_design_version_or_404(project_id: int, site_id: int, version_id: int, db: Session) -> DesignVersion:
    dv = db.get(DesignVersion, version_id)
    if dv is None or dv.site_id != site_id:
        raise HTTPException(status_code=404, detail="Design version not found")
    return dv


@router.post("/{version_id}/validate", response_model=ValidationReportResponse, status_code=201)
def run_validation(project_id: int, site_id: int, version_id: int, db: Session = Depends(get_db)):
    dv = get_design_version_or_404(project_id, site_id, version_id, db)

    import json
    design_data = json.loads(dv.design_json) if isinstance(dv.design_json, str) else dv.design_json

    try:
        canonical = CanonicalDesignVersion.model_validate(design_data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid design data: {exc}")

    analysis = analyze_design(canonical)
    compliance = evaluate_compliance(analysis)

    run = ValidationRun(
        design_version_id=dv.id,
        rule_set_version="1.0.0",
        status=compliance.status.value,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()

    for finding in compliance.findings:
        import json
        result = ValidationResult(
            validation_run_id=run.id,
            rule_id=finding.rule_id,
            status=finding.status.value,
            message=finding.message,
            evidence_json=json.dumps(finding.evidence),
        )
        db.add(result)

    db.commit()
    db.refresh(run)

    log_event(
        db,
        project_id=project_id,
        action="validation_run",
        object_type="validation_run",
        object_id=str(run.id),
        details={
            "design_version_id": version_id,
            "status": compliance.status.value,
            "rule_count": len(compliance.findings),
        },
    )
    db.commit()

    results = db.query(ValidationResult).filter(ValidationResult.validation_run_id == run.id).all()

    return ValidationReportResponse(
        run=ValidationRunResponse.model_validate(run),
        results=[ValidationResultResponse.model_validate(r) for r in results],
        summary=compliance.summary,
    )


@router.get("/{version_id}/validation", response_model=list[ValidationRunResponse])
def list_validations(project_id: int, site_id: int, version_id: int, db: Session = Depends(get_db)):
    get_design_version_or_404(project_id, site_id, version_id, db)
    runs = db.query(ValidationRun).filter(ValidationRun.design_version_id == version_id).order_by(ValidationRun.id.desc()).all()
    return runs
