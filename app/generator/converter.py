
from app.generator.schemas import GenerationCandidate
from app.schemas.design_version import (
    CanonicalDesignVersion,
    DesignConnection,
    DesignMember,
    DesignMetadata,
)


def candidate_to_design_version(
    candidate: GenerationCandidate,
    *,
    version: str,
) -> CanonicalDesignVersion:
    """
    Convert a provider-independent generation candidate into
    Panah's canonical design representation.

    This is the application-owned boundary between generation
    and downstream geometry/validation systems.
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
        DesignConnection(
            id=f"C-{index + 1:03d}",
            a=connection.a,
            b=connection.b,
            type=connection.type,
        )
        for index, connection in enumerate(candidate.connections)
    ]

    return CanonicalDesignVersion(
        schema_version="1.0.0",
        design_type=candidate.design_type,
        version=version,
        span_m=candidate.span_m,
        height_m=candidate.height_m,
        members=members,
        connections=connections,
        metadata=DesignMetadata(
            generator_name=candidate.generation_method,
            generator_version="1.0.0",
        ),
    )