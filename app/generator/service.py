from app.constraints.schemas import ConstraintSet
from app.generator.schemas import GenerationCandidate, GeneratedConnection, GeneratedMember


class LocalGenerationService:
    """
    Fully local Panah candidate generator.

    This is intentionally independent of Alibaba Cloud, Qwen, network APIs,
    credentials, and external model access. It turns the canonical
    ConstraintSet into small parametric roof-truss candidates.

    It is a development/demo generator, not an engineering safety authority.
    """

    def generate(
        self,
        constraints: ConstraintSet,
        *,
        candidate_index: int = 1,
    ) -> GenerationCandidate:
        if constraints.design_target != "roof_truss":
            raise ValueError(
                f"Unsupported generation target: {constraints.design_target}"
            )

        if candidate_index not in (1, 2, 3):
            raise ValueError("candidate_index must be 1, 2, or 3")

        material = constraints.materials[0]
        if material.diameter_m is None:
            raise ValueError(
                f"Material {material.id} requires diameter_m for local generation"
            )

        available_member_length = material.length_m
        site_span = constraints.site.length_m

        if candidate_index == 1:
            # Intentionally direct/site-sized candidate. The validator is
            # responsible for deciding whether its span is acceptable.
            span = site_span
            height = max(0.5, min(1.0, span / 4))
            brace_count = 1

        elif candidate_index == 2:
            # Conservative candidate constrained by available material length.
            span = min(site_span, available_member_length)
            height = max(0.5, min(1.0, span / 4))
            brace_count = 2

        else:
            # Compact alternative for demonstrating multiple candidates.
            span = min(site_span, available_member_length * 0.8)
            height = max(0.5, min(0.9, span / 4))
            brace_count = 2

        members = [
            GeneratedMember(
                id="M1",
                type="beam",
                length_m=span,
                material_id=material.id,
                diameter_m=material.diameter_m,
            )
        ]

        brace_length = max(0.5, min(span / 2, available_member_length))

        for i in range(brace_count):
            members.append(
                GeneratedMember(
                    id=f"B{i + 1}",
                    type="brace",
                    length_m=brace_length,
                    material_id=material.id,
                    diameter_m=material.diameter_m,
                )
            )

        connections = [
            GeneratedConnection(
                a="M1",
                b=member.id,
                type="bolted",
            )
            for member in members[1:]
        ]

        return GenerationCandidate(
            candidate_id=f"LOCAL-{candidate_index:02d}",
            design_type="roof_truss",
            span_m=span,
            height_m=height,
            members=members,
            connections=connections,
        )

    def generate_candidates(
        self,
        constraints: ConstraintSet,
        *,
        count: int = 3,
    ) -> list[GenerationCandidate]:
        if count < 1 or count > 3:
            raise ValueError("count must be between 1 and 3")

        return [
            self.generate(constraints, candidate_index=index)
            for index in range(1, count + 1)
        ]
