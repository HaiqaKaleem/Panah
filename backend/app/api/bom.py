"""Bill of Materials (BOM) API — generate material lists with cost estimates."""

import json
import math

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.constraints.schemas import ConstraintSet
from app.generator.converter import candidate_to_design_version
from app.materials.catalog import get_material_properties
from app.models.constraint_set import ConstraintSetRecord
from app.models.generated_design import GeneratedDesign
from app.schemas.design_version import DesignMember

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["Bill of Materials"],
)


def _build_bom(members: list[DesignMember], constraints: ConstraintSet) -> dict:
    """Build a Bill of Materials from design members and constraints."""
    # Map material_id from constraint set
    material_map = {m.id: m for m in constraints.materials}
    catalog_props = {}

    for mat_constraint in constraints.materials:
        props = get_material_properties(mat_constraint.type)
        if props:
            catalog_props[mat_constraint.type] = props

    bom_lines = []
    total_cost = 0.0
    total_weight_kg = 0.0

    for member in members:
        mat_constraint = material_map.get(member.material_id)
        if mat_constraint is None:
            continue

        props = catalog_props.get(mat_constraint.type)
        if props is None:
            continue

        # Calculate weight
        weight_kg = 0.0
        if member.diameter_m and member.length_m:
            area_m2 = math.pi * (member.diameter_m ** 2) / 4.0
            volume_m3 = area_m2 * member.length_m * props.hollow_section_factor
            weight_kg = volume_m3 * props.density_kg_m3

        # Calculate cost from catalog pricing
        unit_cost = props.unit_cost_usd
        line_cost = unit_cost  # 1 piece per member
        line_weight = weight_kg

        bom_lines.append({
            "member_id": member.id,
            "member_type": member.type,
            "material_id": member.material_id,
            "material_type": mat_constraint.type,
            "material_name": props.display_name,
            "length_m": member.length_m,
            "diameter_m": member.diameter_m,
            "quantity": 1,
            "unit_cost_usd": unit_cost,
            "cost_unit": props.cost_unit,
            "line_cost_usd": round(line_cost, 2),
            "line_weight_kg": round(weight_kg, 2),
            "local_availability": props.local_availability,
            "expected_lifespan_years": props.expected_lifespan_years,
        })

        total_cost += line_cost
        total_weight_kg += weight_kg

    # Aggregate by material type
    by_type = {}
    for line in bom_lines:
        t = line["material_type"]
        if t not in by_type:
            by_type[t] = {
                "type": t,
                "name": line["material_name"],
                "count": 0,
                "total_cost_usd": 0.0,
                "total_weight_kg": 0.0,
                "local_availability": line["local_availability"],
            }
        by_type[t]["count"] += 1
        by_type[t]["total_cost_usd"] += line["line_cost_usd"]
        by_type[t]["total_weight_kg"] += line["line_weight_kg"]

    return {
        "line_items": bom_lines,
        "summary": {
            "total_items": len(bom_lines),
            "total_cost_usd": round(total_cost, 2),
            "total_weight_kg": round(total_weight_kg, 2),
            "by_material_type": [
                {
                    **v,
                    "total_cost_usd": round(v["total_cost_usd"], 2),
                    "total_weight_kg": round(v["total_weight_kg"], 2),
                }
                for v in by_type.values()
            ],
        },
        "cost_note": "Prices are reference estimates for South Asia region. Actual costs vary by location and supplier.",
    }


@router.get("/generated-designs/{design_id}/bom")
def get_bom(design_id: int, project_id: int, site_id: int, db: Session = Depends(get_db)):
    """Generate a Bill of Materials for a generated design."""
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    if cs_record is None:
        raise HTTPException(status_code=404, detail="Constraint set not found")

    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json)
    design_data = json.loads(record.design_json)
    members = [DesignMember.model_validate(m) for m in design_data.get("members", [])]

    return {
        "design_id": design_id,
        "candidate_id": record.candidate_id,
        **_build_bom(members, constraints),
    }


@router.get("/generated-designs/{design_id}/bom/csv")
def get_bom_csv(design_id: int, project_id: int, site_id: int, db: Session = Depends(get_db)):
    """Export BOM as CSV for download."""
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    if cs_record is None:
        raise HTTPException(status_code=404, detail="Constraint set not found")

    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json)
    design_data = json.loads(record.design_json)
    members = [DesignMember.model_validate(m) for m in design_data.get("members", [])]

    bom = _build_bom(members, constraints)

    # Build CSV
    lines = ["Member ID,Type,Material,Length (m),Diameter (m),Qty,Unit Cost (USD),Line Cost (USD),Weight (kg),Availability"]
    for item in bom["line_items"]:
        lines.append(
            f"{item['member_id']},{item['member_type']},{item['material_name']},"
            f"{item['length_m']},{item['diameter_m']},{item['quantity']},"
            f"{item['unit_cost_usd']},{item['line_cost_usd']},"
            f"{item['line_weight_kg']},{item['local_availability']}"
        )

    csv_content = "\n".join(lines)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=bom-design-{design_id}.csv"},
    )
