from app.schemas.design_version import DesignMember
from app.geometry.schemas import (
    GeometryDimensions,
    GeometryPrimitive,
    Vector3,
)


def member_to_primitive(member: DesignMember) -> GeometryPrimitive:
    """
    Convert one canonical design member into a renderer-independent
    geometric primitive.

    This layer deliberately does not create Three.js meshes or GLB files.
    It only creates structured geometry that later renderers can consume.
    """

    member_type = member.type

    if member_type == "beam":
        geometry_type = "beam"
    elif member_type == "brace":
        geometry_type = "brace"
    else:
        raise ValueError(
            f"Unsupported geometry member type: {member_type}"
        )

    dimensions = GeometryDimensions(
        length_m=member.length_m,
        width_m=member.diameter_m,
        height_m=member.diameter_m,
    )

    return GeometryPrimitive(
        component_id=member.id,
        geometry_type=geometry_type,
        material_id=member.material_id,
        position=Vector3(x=0, y=0, z=0),
        rotation=Vector3(x=0, y=0, z=0),
        dimensions=dimensions,
    )
