from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class ProjectCreate(BaseModel):
    name: StrictStr = Field(min_length=1, max_length=160)
    location: StrictStr = Field(min_length=1, max_length=160)

    model_config = ConfigDict(extra="forbid")


class ProjectUpdate(BaseModel):
    # A missing key is allowed. A supplied null is rejected below.
    name: StrictStr | None = Field(default=None, min_length=1, max_length=160)
    location: StrictStr | None = Field(default=None, min_length=1, max_length=160)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name", "location")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    status: str
    created_at: datetime
    updated_at: datetime
