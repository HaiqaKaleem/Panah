from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ShelterType = Literal[
    "temporary",
    "emergency",
    "transitional",
]

DesignPriority = Literal[
    "site_fit",
    "space_efficiency",
    "material_efficiency",
]


class DesignSpecificationUpdate(BaseModel):
    family_size: int = Field(ge=1, le=50)

    shelter_type: ShelterType = "temporary"

    required_spaces: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    maximum_footprint_m2: float | None = Field(
        default=None,
        gt=0,
        le=1000,
    )

    maximum_height_m: float | None = Field(
        default=None,
        gt=0,
        le=20,
    )

    available_materials: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    preferred_materials: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    priorities: list[DesignPriority] = Field(
        default_factory=list,
        max_length=3,
    )

    coordinator_notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "required_spaces",
        "available_materials",
        "preferred_materials",
    )
    @classmethod
    def clean_lists(cls, values):
        cleaned = []
        for value in values:
            value = value.strip()
            if value and value not in cleaned:
                cleaned.append(value)
        return cleaned

    @field_validator("priorities")
    @classmethod
    def unique_priorities(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("priorities must be unique")
        return values


class DesignSpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    status: str
    specification_json: str
    created_at: datetime
    updated_at: datetime
