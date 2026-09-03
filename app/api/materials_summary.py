"""Materials summary API — aggregate metrics for the Materials screen."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.models.material import Material
from app.materials.catalog import get_material_properties

router = APIRouter(prefix="/projects/{project_id}/materials-summary", tags=["Materials Summary"])


def _get_project_or_404(project_id: int, db: Session) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("")
def get_materials_summary(project_id: int, db: Session = Depends(get_db)):
    """
    Return aggregate material metrics for a project:
    - Total item count
    - Total estimated weight (kg)
    - Breakdown by material type
    """
    _get_project_or_404(project_id, db)

    materials = (
        db.query(Material)
        .filter(Material.project_id == project_id)
        .all()
    )

    if not materials:
        return {
            "project_id": project_id,
            "total_items": 0,
            "total_weight_kg": 0.0,
            "by_type": [],
        }

    total_weight = 0.0
    type_breakdown: dict[str, dict] = {}

    for mat in materials:
        props = get_material_properties(mat.type)
        weight_kg = 0.0

        if props and mat.length_m and mat.diameter_m:
            # Estimate weight from circular cross-section * length * density
            import math
            area_m2 = math.pi * (mat.diameter_m ** 2) / 4.0
            volume_m3 = area_m2 * mat.length_m * props.hollow_section_factor
            weight_kg = volume_m3 * props.density_kg_m3 * mat.quantity
        elif props and mat.length_m:
            # Estimate weight from linear density approximation
            import math
            area_m2 = math.pi * (0.05 ** 2) / 4.0  # assume 50mm diameter
            volume_m3 = area_m2 * mat.length_m * props.hollow_section_factor
            weight_kg = volume_m3 * props.density_kg_m3 * mat.quantity

        total_weight += weight_kg

        if mat.type not in type_breakdown:
            type_breakdown[mat.type] = {
                "type": mat.type,
                "display_name": props.display_name if props else mat.type,
                "count": 0,
                "total_quantity": 0,
                "estimated_weight_kg": 0.0,
            }
        type_breakdown[mat.type]["count"] += 1
        type_breakdown[mat.type]["total_quantity"] += mat.quantity
        type_breakdown[mat.type]["estimated_weight_kg"] += weight_kg

    return {
        "project_id": project_id,
        "total_items": len(materials),
        "total_weight_kg": round(total_weight, 2),
        "by_type": [
            {
                **v,
                "estimated_weight_kg": round(v["estimated_weight_kg"], 2),
            }
            for v in type_breakdown.values()
        ],
    }
