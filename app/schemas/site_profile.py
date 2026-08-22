from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProfileStatus = Literal["draft", "ready"]


class SiteProfileUpdate(BaseModel):
    terrain: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    access: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    geometry: dict = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class SiteProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    status: str
    profile_json: str
    created_at: datetime
    updated_at: datetime
