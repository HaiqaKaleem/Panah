from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class SiteCreate(BaseModel):
    name: StrictStr = Field(min_length=1, max_length=160)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    model_config = ConfigDict(extra="forbid")

    @field_validator("latitude", "longitude")
    @classmethod
    def reject_nan(cls, value):
        if value is not None and value != value:
            raise ValueError("coordinate cannot be NaN")
        return value


class SiteUpdate(BaseModel):
    name: StrictStr | None = Field(default=None, min_length=1, max_length=160)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def reject_null_name(cls, value):
        if value is None:
            raise ValueError("name cannot be null")
        return value


class SiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    latitude: float | None
    longitude: float | None
    status: str
    created_at: datetime
    updated_at: datetime


class CaptureCreate(BaseModel):
    captured_at: datetime
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    notes: StrictStr | None = Field(default=None, max_length=5000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("latitude", "longitude")
    @classmethod
    def reject_nan(cls, value):
        if value is not None and value != value:
            raise ValueError("coordinate cannot be NaN")
        return value


class CaptureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    captured_at: datetime
    latitude: float | None
    longitude: float | None
    status: str
    notes: str | None
    created_at: datetime
