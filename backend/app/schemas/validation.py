from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ValidationStatus = Literal["pass", "fail", "review", "running", "error"]


class ValidationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    design_version_id: int
    rule_set_version: str
    status: str
    started_at: datetime
    completed_at: datetime | None


class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    validation_run_id: int
    rule_id: str
    status: str
    message: str
    evidence_json: str | None
    created_at: datetime


class ValidationReportResponse(BaseModel):
    run: ValidationRunResponse
    results: list[ValidationResultResponse]
    summary: dict
