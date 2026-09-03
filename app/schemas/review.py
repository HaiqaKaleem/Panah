from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ReviewDecision = Literal["approve", "reject", "request_changes", "pending"]


class ReviewCreate(BaseModel):
    reviewer_id: str = Field(default="engineer", max_length=100)
    model_config = ConfigDict(extra="forbid")


class ReviewDecisionUpdate(BaseModel):
    decision: ReviewDecision
    comments: str | None = Field(default=None, max_length=2000)
    model_config = ConfigDict(extra="forbid")


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    design_version_id: int
    reviewer_id: str
    decision: str
    comments: str | None
    created_at: datetime
    updated_at: datetime
