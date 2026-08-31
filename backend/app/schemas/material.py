from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaterialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=0)
    unit: str = Field(default="pieces", max_length=20)
    length_m: float | None = Field(default=None, gt=0)
    diameter_m: float | None = Field(default=None, gt=0)

    model_config = ConfigDict(extra="forbid")


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    type: str
    quantity: int
    unit: str
    length_m: float | None
    diameter_m: float | None
    created_at: datetime
