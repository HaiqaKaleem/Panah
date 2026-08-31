from app.design.base import GenerationInput


class MockDesignGenerator:
    """
    Development generator.

    Produces a simple parametric candidate from the specification.
    It is NOT an AI model and does NOT claim structural safety.
    """

    name = "mock-parametric-generator"
    version = "1.0"

    def generate(self, generation_input: GenerationInput) -> dict:
        spec = generation_input.design_specification

        family_size = spec["family_size"]
        maximum_footprint = spec.get("maximum_footprint_m2")
        maximum_height = spec.get("maximum_height_m")

        # Simple deterministic demo dimensions.
        target_area = maximum_footprint or max(12.0, family_size * 3.5)
        width = round(target_area ** 0.5, 2)
        depth = round(target_area / width, 2)
        height = min(maximum_height or 3.0, 3.0)

        materials = spec.get("preferred_materials") or spec.get(
            "available_materials"
        ) or ["unspecified"]

        primary_material = materials[0]

        return {
            "name": f"Panagah Candidate {family_size}P",
            "footprint_m2": round(width * depth, 2),
            "overall_height_m": height,
            "components": [
                {
                    "component_id": "floor-01",
                    "component_type": "floor",
                    "material": primary_material,
                    "position": {"x": 0, "y": 0, "z": 0},
                    "dimensions": {
                        "width_m": width,
                        "depth_m": depth,
                        "height_m": 0.10,
                    },
                },
                {
                    "component_id": "frame-01",
                    "component_type": "frame",
                    "material": primary_material,
                    "position": {"x": 0, "y": 0, "z": 0},
                    "dimensions": {
                        "width_m": width,
                        "depth_m": depth,
                        "height_m": height,
                    },
                },
                {
                    "component_id": "roof-01",
                    "component_type": "roof",
                    "material": primary_material,
                    "position": {
                        "x": 0,
                        "y": 0,
                        "z": height,
                    },
                    "dimensions": {
                        "width_m": width,
                        "depth_m": depth,
                        "height_m": 0.20,
                    },
                },
            ],
            "generation_notes": (
                "Development-only parametric candidate. "
                "No structural safety conclusion has been made."
            ),
        }
