from pydantic import BaseModel, ConfigDict, Field


class OccupancyConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    people: int = Field(..., ge=1)


class SiteConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_m: float = Field(..., gt=0)
    width_m: float = Field(..., gt=0)


class MaterialConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    qty: float = Field(..., gt=0)
    length_m: float = Field(..., gt=0)
    diameter_m: float | None = Field(default=None, gt=0)


class EnvironmentConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(..., min_length=1)


class ConstraintSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"
    version: str = Field(..., min_length=1)
    occupancy: OccupancyConstraint
    site: SiteConstraint
    materials: list[MaterialConstraint] = Field(..., min_length=1)
    environment: EnvironmentConstraint
    design_target: str = Field(..., min_length=1)
    unknowns: list[str] = Field(default_factory=list)