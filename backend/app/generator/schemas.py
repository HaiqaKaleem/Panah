from pydantic import BaseModel, ConfigDict, Field


class GeneratedMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    length_m: float = Field(..., gt=0)
    material_id: str = Field(..., min_length=1)
    diameter_m: float | None = Field(default=None, gt=0)


class GeneratedConnection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    a: str = Field(..., min_length=1)
    b: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)


class GenerationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    design_type: str = Field(..., min_length=1)
    span_m: float = Field(..., gt=0)
    height_m: float = Field(..., gt=0)
    members: list[GeneratedMember] = Field(..., min_length=1)
    connections: list[GeneratedConnection] = Field(default_factory=list)
    generation_method: str = "local_constraint_generator"
