from app.generator.schemas import GenerationCandidate
from app.schemas.design_version import CanonicalDesignVersion, DesignMember


def candidate_to_design_version(
    candidate: GenerationCandidate,
    *,
    version: str,
) -> CanonicalDesignVersion:
    """
    Convert provider/local candidate data into Panah's canonical design model.

    This is the application-owned boundary: once converted, downstream
    geometry and validation operate on CanonicalDesignVersion rather than
    generator-specific objects.
    """
    members = [
        DesignMember(
            id=member.id,
            type=member.type,
            material_id=member.material_id,
            length_m=member.length_m,
            diameter_m=member.diameter_m,
        )
        for member in candidate.members
    ]

    connections = [
        {
            "a": connection.a,
            "b": connection.b,
            "type": connection.type,
        }
        for connection in candidate.connections
    ]

    return CanonicalDesignVersion(
        schema_version="1.0.0",
        design_type=candidate.design_type,
        version=version,
        span_m=candidate.span_m,
        height_m=candidate.height_m,
        members=members,
        connections=connections,
    )
