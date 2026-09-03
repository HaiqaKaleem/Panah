"""Export API — download design data for sharing with engineers."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.generated_design import GeneratedDesign
from app.models.design_version import DesignVersion
from app.models.constraint_set import ConstraintSetRecord
from app.constraints.schemas import ConstraintSet
from app.rules import evaluate_structural_rules, get_sphere_rules
from app.structural.analysis import analyze_structure

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Export"],
)


@router.get("/generated-designs/{design_id}/export")
def export_generated_design(
    design_id: int,
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    """
    Export a generated design as a comprehensive JSON package.
    Includes design data, analysis, rules, constraint set, and metadata.
    """
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json) if cs_record else None

    export_data = {
        "export_version": "1.0.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "site_id": site_id,
        "design_id": design_id,
        "candidate_id": record.candidate_id,
        "version": record.version,
        "status": record.status,
        "design": json.loads(record.design_json),
        "analysis": json.loads(record.analysis_json),
        "rules": json.loads(record.rules_json),
        "constraint_set": constraints.model_dump() if constraints else None,
        "sphere_rules_catalog": [r.to_dict() for r in get_sphere_rules()],
        "metadata": {
            "generator": "Panah Local Generation Engine",
            "generator_version": "1.0.0",
            "structural_analysis_version": "1.0.0",
            "standards": "Sphere Handbook V24.1",
            "export_note": "Reference prescreening results. Engineering verification required before construction.",
        },
    }

    content = json.dumps(export_data, indent=2, default=str)

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=panah-design-{design_id}.json",
        },
    )


@router.get("/design-versions/{version_id}/export")
def export_design_version(
    version_id: int,
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    """Export a design version as JSON."""
    dv = db.get(DesignVersion, version_id)
    if dv is None or dv.site_id != site_id:
        raise HTTPException(status_code=404, detail="Design version not found")

    export_data = {
        "export_version": "1.0.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "design_version": {
            "id": dv.id,
            "version": dv.version,
            "schema_version": dv.schema_version,
            "design_type": dv.design_type,
            "status": dv.status,
            "design": json.loads(dv.design_json),
        },
        "metadata": {
            "generator": "Panah API",
            "standards": "Sphere Handbook V24.1",
            "export_note": "Canonical design version. Subject to engineer review.",
        },
    }

    content = json.dumps(export_data, indent=2, default=str)

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=panah-dv-{version_id}.json",
        },
    )
