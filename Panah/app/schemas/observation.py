from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

ObservationType = Literal["site_geometry", "terrain", "object", "access", "material", "condition"]
ObservationStatus = Literal["unconfirmed", "confirmed", "rejected"]

class ObservationCreate(BaseModel):
    observation_type: ObservationType
    label: StrictStr = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)
    bbox_x: float | None = Field(default=None, ge=0, le=1)
    bbox_y: float | None = Field(default=None, ge=0, le=1)
    bbox_width: float | None = Field(default=None, gt=0, le=1)
    bbox_height: float | None = Field(default=None, gt=0, le=1)
    evidence_timestamp_seconds: float | None = Field(default=None, ge=0)
    analysis_metadata: dict | None = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("label")
    @classmethod
    def strip_label(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("label cannot be empty")
        return value

class ObservationStatusUpdate(BaseModel):
    status: ObservationStatus
    model_config = ConfigDict(extra="forbid")

class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    media_id: int
    observation_type: str
    label: str
    confidence: float
    status: str
    bbox_x: float | None
    bbox_y: float | None
    bbox_width: float | None
    bbox_height: float | None
    evidence_timestamp_seconds: float | None
    analysis_metadata_json: str | None
    created_at: datetime
