from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DesignType = Literal["roof_truss", "wall_panel", "frame", "shelter_component"]
MemberType = Literal["beam", "brace", "column", "panel", "connector", "rafter"]
ConnectionType = Literal["bolted", "screwed", "lashed", "welded", "hinged", "other"]


class DesignPoint3D(BaseModel):
    x_m: float
    y_m: float
    z_m: float

    model_config = ConfigDict(extra="forbid")


class DesignDimensions(BaseModel):
    length_m: float = Field(gt=0, le=100)
    width_m: float = Field(gt=0, le=100)
    height_m: float = Field(gt=0, le=100)

    model_config = ConfigDict(extra="forbid")


class DesignMember(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    type: MemberType
    material_id: str = Field(min_length=1, max_length=100)
    start: DesignPoint3D | None = None
    end: DesignPoint3D | None = None
    length_m: float | None = Field(default=None, gt=0, le=100)
    diameter_m: float | None = Field(default=None, gt=0, le=5)
    dimensions: DesignDimensions | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_geometry(self):
        if self.start is not None and self.end is not None:
            if self.start == self.end:
                raise ValueError("start and end points cannot be identical")
        if self.length_m is None and self.start is None and self.dimensions is None:
            raise ValueError("member requires length_m, start/end, or dimensions")
        return self


class DesignConnection(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    a: str = Field(min_length=1, max_length=100)
    b: str = Field(min_length=1, max_length=100)
    type: ConnectionType

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_endpoints(self):
        if self.a == self.b:
            raise ValueError("connection endpoints must be different")
        return self


class DesignMetadata(BaseModel):
    generator_name: str = Field(min_length=1, max_length=100)
    generator_version: str = Field(min_length=1, max_length=100)
    source_constraint_set_id: str | None = Field(default=None, max_length=100)

    model_config = ConfigDict(extra="forbid")


class CanonicalDesignVersion(BaseModel):
    """Canonical, provider-independent representation of a generated design.

    This is the source representation that future geometry and validation services
    consume. It intentionally contains no validation verdict or engineering approval.
    """

    schema_version: str = Field(default="1.0.0", min_length=1, max_length=20)
    design_type: DesignType
    version: str = Field(default="DV-001", min_length=1, max_length=100)
    span_m: float = Field(gt=0, le=100)
    height_m: float = Field(gt=0, le=100)
    footprint: DesignDimensions | None = None
    members: list[DesignMember] = Field(min_length=1, max_length=500)
    connections: list[DesignConnection] = Field(default_factory=list, max_length=1000)
    metadata: DesignMetadata

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str):
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError("schema_version must use semantic version format, e.g. 1.0.0")
        return value

    @model_validator(mode="after")
    def validate_references(self):
        member_ids = {member.id for member in self.members}
        if len(member_ids) != len(self.members):
            raise ValueError("member IDs must be unique")

        connection_ids = {connection.id for connection in self.connections}
        if len(connection_ids) != len(self.connections):
            raise ValueError("connection IDs must be unique")

        for connection in self.connections:
            if connection.a not in member_ids or connection.b not in member_ids:
                raise ValueError(
                    f"connection {connection.id} references an unknown member"
                )

        return self
