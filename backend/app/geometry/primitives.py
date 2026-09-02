from app.geometry.schemas import GeometryDimensions, GeometryPrimitive, Vector3
from app.schemas.design_version import DesignMember

SUPPORTED_MEMBER_TYPES = {"beam", "brace"}

def member_to_primitive(member: DesignMember) -> GeometryPrimitive:
    """Convert one canonical design member into renderer-independent geometry."""
    if member.type not in SUPPORTED_MEMBER_TYPES:
        raise ValueError(f"Unsupported geometry member type: {member.type}")

    diameter = member.diameter_m
    if diameter is None:
        raise ValueError(f"Member {member.id} requires diameter_m for geometry generation")

    return GeometryPrimitive(
        component_id=member.id,
        geometry_type=member.type,
        material_id=member.material_id,
        position=Vector3(x=0, y=0, z=0),
        rotation=Vector3(x=0, y=0, z=0),
        dimensions=GeometryDimensions(
            length_m=member.length_m,
            width_m=diameter,
            height_m=diameter,
        ),
    )
