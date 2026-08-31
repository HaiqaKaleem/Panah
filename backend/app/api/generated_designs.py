import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.generated_design import GeneratedDesign
from app.models.design_version import DesignVersion
from app.services.audit import log_event
from app.services.design_versions import DesignVersionConflictError

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Generated Design Promotion"],
)


@router.post(
    "/generated-designs/{design_id}/promote",
    status_code=201,
)
def promote_generated_design(
    project_id: int,
    site_id: int,
    design_id: int,
    db: Session = Depends(get_db),
):
    """
    Promote a GeneratedDesign to a persisted DesignVersion.

    This connects the constraint-set generation flow to the
    validation/review flow. After promotion, the design version
    can be validated, reviewed, and tracked through the full pipeline.
    """
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    # Check for existing promoted version
    existing = (
        db.query(DesignVersion)
        .filter(
            DesignVersion.site_id == site_id,
            DesignVersion.version == record.version,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Design version {record.version} already exists for this site.",
        )

    design_data = json.loads(record.design_json)

    design_version = DesignVersion(
        site_id=site_id,
        design_specification_id=0,  # constraint-set path has no spec
        source_candidate_id=None,
        version=record.version,
        schema_version=design_data.get("schema_version", "1.0"),
        design_type=design_data.get("design_type", "roof_truss"),
        status="draft",
        design_json=record.design_json,
    )
    db.add(design_version)
    db.flush()

    # Update the generated design status
    record.status = "promoted"
    db.commit()
    db.refresh(design_version)

    log_event(
        db,
        project_id=project_id,
        action="generated_design_promoted",
        object_type="design_version",
        object_id=str(design_version.id),
        details={
            "generated_design_id": design_id,
            "candidate_id": record.candidate_id,
            "version": record.version,
        },
    )
    db.commit()

    return {
        "id": design_version.id,
        "site_id": design_version.site_id,
        "version": design_version.version,
        "schema_version": design_version.schema_version,
        "design_type": design_version.design_type,
        "status": design_version.status,
        "design_json": json.loads(design_version.design_json),
        "promoted_from": design_id,
    }
