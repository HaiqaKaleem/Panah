from fastapi import APIRouter, Query

from app.materials.catalog import MATERIAL_CATALOG

router = APIRouter(prefix="/material-catalog", tags=["Material Catalog"])


def _classify_category(mat_type: str) -> str:
    """Infer a user-facing category from the material type."""
    if mat_type in ("treated_bamboo", "reclaimed_timber"):
        return "Structural"
    if mat_type == "stabilized_mud_brick":
        return "Foundation"
    if mat_type == "corrugated_tin":
        return "Cladding"
    if mat_type == "steel_connector":
        return "Hardware"
    return "Other"


def _is_locally_sourced(mat_type: str) -> bool:
    """Heuristic for local sourcing availability."""
    return mat_type in ("treated_bamboo", "reclaimed_timber", "stabilized_mud_brick")


@router.get("")
def list_material_catalog(
    category: str | None = Query(default=None, description="Filter by category: Structural, Foundation, Cladding, Hardware"),
    sort_by: str | None = Query(default=None, description="Sort by: density, modulus, lifespan, yield_strength"),
    min_lifespan_years: float | None = Query(default=None, description="Minimum expected lifespan in years"),
):
    """Return available material types with filtering and sorting for the Material Library screen."""
    materials = []
    for mat in MATERIAL_CATALOG.values():
        cat = _classify_category(mat.type)
        locally_sourced = _is_locally_sourced(mat.type)

        # Apply category filter
        if category and cat.lower() != category.lower():
            continue

        # Apply lifespan filter
        if min_lifespan_years is not None and mat.expected_lifespan_years < min_lifespan_years:
            continue

        materials.append({
            "type": mat.type,
            "display_name": mat.display_name,
            "category": cat,
            "locally_sourced": locally_sourced,
            "density_kg_m3": mat.density_kg_m3,
            "elastic_modulus_pa": mat.elastic_modulus_pa,
            "allowable_bending_stress_pa": mat.allowable_bending_stress_pa,
            "allowable_axial_stress_pa": mat.allowable_axial_stress_pa,
            "expected_lifespan_years": mat.expected_lifespan_years,
            "hollow_section_factor": mat.hollow_section_factor,
            "source": mat.source,
        })

    # Apply sorting
    sort_keys = {
        "density": lambda m: m["density_kg_m3"],
        "modulus": lambda m: m["elastic_modulus_pa"],
        "lifespan": lambda m: m["expected_lifespan_years"],
        "yield_strength": lambda m: m["allowable_bending_stress_pa"],
    }
    if sort_by and sort_by in sort_keys:
        materials.sort(key=sort_keys[sort_by])

    # Categories summary
    categories = sorted(set(m["category"] for m in materials))

    return {
        "count": len(materials),
        "categories": categories,
        "materials": materials,
    }


@router.get("/{material_type}")
def get_material_detail(material_type: str):
    """Return engineering properties for a specific material type."""
    from fastapi import HTTPException

    mat = MATERIAL_CATALOG.get(material_type)
    if mat is None:
        raise HTTPException(status_code=404, detail=f"Material type '{material_type}' not found")

    return {
        "type": mat.type,
        "display_name": mat.display_name,
        "density_kg_m3": mat.density_kg_m3,
        "elastic_modulus_pa": mat.elastic_modulus_pa,
        "allowable_bending_stress_pa": mat.allowable_bending_stress_pa,
        "allowable_axial_stress_pa": mat.allowable_axial_stress_pa,
        "expected_lifespan_years": mat.expected_lifespan_years,
        "hollow_section_factor": mat.hollow_section_factor,
        "source": mat.source,
    }
