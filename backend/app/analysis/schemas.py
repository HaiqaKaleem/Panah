
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalysisFindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AnalysisFindingStatus(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


class AnalysisFinding(BaseModel):
    """
    A deterministic engineering-analysis observation.

    This is deliberately different from a standards verdict.
    The analysis engine reports what it found; the standards layer
    decides whether those findings satisfy a particular standard.
    """

    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    severity: AnalysisFindingSeverity
    status: AnalysisFindingStatus
    message: str = Field(min_length=1, max_length=1000)
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class MemberAnalysis(BaseModel):
    """Computed deterministic metrics for one design member."""

    member_id: str = Field(min_length=1, max_length=100)
    member_type: str = Field(min_length=1, max_length=50)
    material_id: str = Field(min_length=1, max_length=100)

    length_m: float | None = Field(default=None, ge=0)
    geometric_length_m: float | None = Field(default=None, ge=0)

    diameter_m: float | None = Field(default=None, ge=0)
    volume_m3: float | None = Field(default=None, ge=0)

    geometry_complete: bool
    connected: bool

    model_config = ConfigDict(extra="forbid")


class AnalysisSummary(BaseModel):
    """Aggregate deterministic analysis metrics."""

    member_count: int = Field(ge=0)
    connection_count: int = Field(ge=0)

    total_member_length_m: float = Field(ge=0)
    total_member_volume_m3: float = Field(ge=0)

    connected_member_count: int = Field(ge=0)
    disconnected_member_count: int = Field(ge=0)

    complete_geometry_member_count: int = Field(ge=0)
    incomplete_geometry_member_count: int = Field(ge=0)

    finding_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class AnalysisResult(BaseModel):
    """
    Complete deterministic analysis output for a canonical design.

    No safety approval is implied by this object.
    """

    analysis_version: str = Field(default="1.0.0", min_length=1, max_length=20)

    design_version: str = Field(min_length=1, max_length=100)
    design_type: str = Field(min_length=1, max_length=50)

    status: str = Field(min_length=1, max_length=50)

    summary: AnalysisSummary
    members: list[MemberAnalysis] = Field(default_factory=list)
    findings: list[AnalysisFinding] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @property
    def has_errors(self) -> bool:
        return self.summary.error_count > 0

    @property
    def requires_review(self) -> bool:
        return self.summary.error_count > 0 or self.summary.warning_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_version": self.analysis_version,
            "design_version": self.design_version,
            "design_type": self.design_type,
            "status": self.status,
            "summary": self.summary.model_dump(),
            "members": [
                member.model_dump()
                for member in self.members
            ],
            "findings": [
                finding.model_dump(mode="json")
                for finding in self.findings
            ],
            "has_errors": self.has_errors,
            "requires_review": self.requires_review,
        }