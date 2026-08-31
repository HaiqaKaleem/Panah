
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.design_version import CanonicalDesignVersion
from app.services.design_versions import (
    DesignCandidateNotFoundError,
    DesignVersionConflictError,
    create_design_version_from_candidate,
    get_design_version,
    list_design_versions,
)


router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}/design-versions",
    tags=["Design Versions"],
)


class DesignVersionResponse(BaseModel):
    id: int
    site_id: int
    design_specification_id: int | None = None
    source_candidate_id: int
    version: str
    schema_version: str
    design_type: str
    status: str
    design_json: dict


def _design_json_payload(record) -> dict:
    if isinstance(record.design_json, dict):
        return record.design_json

    return json.loads(record.design_json)


def _to_response(record) -> DesignVersionResponse:
    return DesignVersionResponse(
        id=record.id,
        site_id=record.site_id,
        design_specification_id=record.design_specification_id,
        source_candidate_id=record.source_candidate_id,
        version=record.version,
        schema_version=record.schema_version,
        design_type=record.design_type,
        status=record.status,
        design_json=_design_json_payload(record),
    )


@router.post(
    "/from-candidate/{candidate_id}",
    response_model=DesignVersionResponse,
    status_code=201,
)
def create_version_from_candidate(
    project_id: int,
    site_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """
    Create and persist a canonical design version
    from an existing design candidate.
    """

    try:
        record = create_design_version_from_candidate(
            db,
            candidate_id,
        )

    except DesignCandidateNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except DesignVersionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if record.site_id != site_id:
        raise HTTPException(
            status_code=404,
            detail="Design candidate does not belong to this site.",
        )

    return _to_response(record)


@router.get(
    "",
    response_model=list[DesignVersionResponse],
)
def get_versions(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
):
    """
    List persisted canonical design versions for a site.
    """

    records = list_design_versions(
        db,
        site_id=site_id,
    )

    return [
        _to_response(record)
        for record in records
    ]


@router.get(
    "/{version_id}",
    response_model=DesignVersionResponse,
)
def get_version(
    project_id: int,
    site_id: int,
    version_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a persisted canonical design version.
    """

    record = get_design_version(
        db,
        version_id,
    )

    if record is None or record.site_id != site_id:
        raise HTTPException(
            status_code=404,
            detail=f"Design version {version_id} was not found.",
        )

    return _to_response(record)