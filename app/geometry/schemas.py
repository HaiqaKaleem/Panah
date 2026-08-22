from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


GeometryType = Literal["beam", "brace", "panel"]


class Vector3(BaseModel):
    x: float
    y: float
    z: float

    model_config = ConfigDict(extra="forbid")


class GeometryDimensions(BaseModel):
    length_m: float | None = Field(default=None, gt=0)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    thickness_m: float | None = Field(default=None, gt=0)

    model_config = ConfigDict(extra="forbid")


class GeometryPrimitive(BaseModel):
    component_id: str = Field(min_length=1, max_length=100)
    geometry_type: GeometryType
    material_id: str = Field(min_length=1, max_length=100)
    position: Vector3
    rotation: Vector3 = Field(default_factory=lambda: Vector3(x=0, y=0, z=0))
    dimensions: GeometryDimensions

    model_config = ConfigDict(extra="forbid")


class GeometryBuildResult(BaseModel):
    design_version_id: str
    primitives: list[GeometryPrimitive]

    model_config = ConfigDict(extra="forbid")
