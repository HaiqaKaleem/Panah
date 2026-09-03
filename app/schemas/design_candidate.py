from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


CandidateStatus = Literal[
    "generated",
    "selected",
    "rejected",
]

ComponentType = Literal[
    "floor",
    "wall_panel",
    "roof",
    "roof_truss",
    "door",
    "window",
    "frame",
]


class Point3D(BaseModel):
    x: float
    y: float
    z: float


class Dimension3D(BaseModel):
    width_m: float = Field(gt=0, le=100)
    depth_m: float = Field(gt=0, le=100)
    height_m: float = Field(gt=0, le=30)


class DesignComponent(BaseModel):
    component_id: str = Field(min_length=1, max_length=100)
    component_type: ComponentType
    material: str = Field(min_length=1, max_length=100)
    position: Point3D
    dimensions: Dimension3D

    model_config = ConfigDict(extra="forbid")


class DesignCandidatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    footprint_m2: float = Field(gt=0, le=10000)
    overall_height_m: float = Field(gt=0, le=30)

    components: list[DesignComponent] = Field(
        min_length=1,
        max_length=500,
    )

    generation_notes: str | None = Field(
        default=None,
        max_length=3000,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        return value


class DesignCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    design_specification_id: int
    status: str
    generator_name: str
    generator_version: str | None
    candidate_json: str
    input_snapshot_json: str
    created_at: datetime
