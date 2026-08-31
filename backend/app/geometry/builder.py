from app.geometry.primitives import member_to_primitive
from app.geometry.schemas import GeometryBuildResult
from app.schemas.design_version import CanonicalDesignVersion

SUPPORTED_DESIGN_TYPES = {"roof_truss"}

def build_geometry(design: CanonicalDesignVersion) -> GeometryBuildResult:
    """Convert a canonical design into renderer-independent geometry primitives."""
    if design.design_type not in SUPPORTED_DESIGN_TYPES:
        raise ValueError(f"Unsupported design type: {design.design_type}")

    return GeometryBuildResult(
        design_version_id=design.version,
        primitives=[member_to_primitive(member) for member in design.members],
    )
