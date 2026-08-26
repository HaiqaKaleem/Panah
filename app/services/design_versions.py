
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.design_candidate import DesignCandidate
from app.models.design_version import DesignVersion


class DesignVersionError(Exception):
    """Base error for design version operations."""


class DesignCandidateNotFoundError(DesignVersionError):
    """Raised when the requested design candidate does not exist."""


class DesignVersionConflictError(DesignVersionError):
    """Raised when a design version would duplicate an existing version."""


def _candidate_payload(candidate: DesignCandidate) -> dict:
    """
    Extract the canonical design payload from a DesignCandidate.
    """

    if hasattr(candidate, "design_json"):
        value = candidate.design_json

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            return json.loads(value)

    if hasattr(candidate, "candidate_json"):
        value = candidate.candidate_json

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            return json.loads(value)

    return {}


def create_design_version_from_candidate(
    db: Session,
    candidate_id: int,
    version: str | None = None,
) -> DesignVersion:
    """
    Create a canonical DesignVersion from an existing DesignCandidate.

    The candidate is the source of the persisted design definition.
    """

    candidate = db.get(DesignCandidate, candidate_id)

    if candidate is None:
        raise DesignCandidateNotFoundError(
            f"Design candidate {candidate_id} was not found."
        )

    payload = _candidate_payload(candidate)

    requested_version = version

    if requested_version is None:
        requested_version = (
            getattr(candidate, "version", None)
            or getattr(candidate, "candidate_version", None)
            or "1.0.0"
        )

    existing = db.scalar(
        select(DesignVersion).where(
            DesignVersion.site_id == candidate.site_id,
            DesignVersion.version == requested_version,
        )
    )

    if existing is not None:
        raise DesignVersionConflictError(
            f"Design version {requested_version} already exists "
            f"for site {candidate.site_id}."
        )

    design_version = DesignVersion(
        site_id=candidate.site_id,
        source_candidate_id=candidate.id,
        version=requested_version,
        design_json=json.dumps(payload, sort_keys=True),
    )

    if hasattr(candidate, "design_specification_id"):
        design_version.design_specification_id = (
            candidate.design_specification_id
        )

    if hasattr(design_version, "schema_version"):
        design_version.schema_version = payload.get(
            "schema_version",
            "1.0",
        )

    if hasattr(design_version, "design_type"):
        design_version.design_type = payload.get(
            "design_type",
            "canonical",
        )

    if hasattr(design_version, "status"):
        design_version.status = "draft"

    db.add(design_version)
    db.commit()
    db.refresh(design_version)

    return design_version


def get_design_version(
    db: Session,
    version_id: int,
) -> DesignVersion | None:
    """
    Return a persisted DesignVersion by primary key.
    """

    return db.get(DesignVersion, version_id)


def list_design_versions(
    db: Session,
    site_id: int | None = None,
) -> list[DesignVersion]:
    """
    List persisted canonical design versions.
    """

    statement = select(DesignVersion)

    if site_id is not None:
        statement = statement.where(
            DesignVersion.site_id == site_id
        )

    return list(
        db.scalars(
            statement.order_by(DesignVersion.id.desc())
        ).all()
    )