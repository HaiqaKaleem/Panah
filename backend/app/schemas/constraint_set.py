import json

from pydantic import BaseModel, Field

from app.constraints.schemas import ConstraintSet


class ConstraintSetResponse(BaseModel):
    id: int
    site_id: int
    version: str
    constraints: ConstraintSet


class GenerateRequest(BaseModel):
    count: int = Field(default=3, ge=1, le=3)


class GeneratedDesignSummary(BaseModel):
    """Lightweight summary for a list view (Build screen candidate picker)."""

    id: int
    candidate_id: str
    version: str
    status: str
    overall_integrity_score: float | None
    compliant: bool
    score: float
    blocking_rule_count: int


class GeneratedDesignDetail(BaseModel):
    """Full detail for one generated design (Build screen deep dive)."""

    id: int
    site_id: int
    candidate_id: str
    version: str
    status: str
    design: dict
    analysis: dict
    rules: dict


def constraint_set_to_response(record) -> ConstraintSetResponse:
    return ConstraintSetResponse(
        id=record.id,
        site_id=record.site_id,
        version=record.version,
        constraints=ConstraintSet.model_validate_json(record.constraint_json),
    )


def generated_design_to_summary(record) -> GeneratedDesignSummary:
    rules = json.loads(record.rules_json)
    analysis = json.loads(record.analysis_json)
    return GeneratedDesignSummary(
        id=record.id,
        candidate_id=record.candidate_id,
        version=record.version,
        status=record.status,
        overall_integrity_score=analysis.get("overall_integrity_score"),
        compliant=rules["compliant"],
        score=rules["score"],
        blocking_rule_count=rules["summary"]["blocking"],
    )


def generated_design_to_detail(record) -> GeneratedDesignDetail:
    return GeneratedDesignDetail(
        id=record.id,
        site_id=record.site_id,
        candidate_id=record.candidate_id,
        version=record.version,
        status=record.status,
        design=json.loads(record.design_json),
        analysis=json.loads(record.analysis_json),
        rules=json.loads(record.rules_json),
    )
