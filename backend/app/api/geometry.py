"""Geometry Export API — professional 3D scene data for Three.js viewer."""

import json
import math

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.geometry.truss_builder import build_simple_truss, build_full_shelter
from app.materials.catalog import MATERIAL_CATALOG
from app.models.generated_design import GeneratedDesign
from app.models.constraint_set import ConstraintSetRecord
from app.constraints.schemas import ConstraintSet
from app.schemas.design_version import CanonicalDesignVersion

router = APIRouter(
    prefix="/projects/{project_id}/sites/{site_id}",
    tags=["3D Geometry"],
)


# Material colors for the 3D viewer
MATERIAL_COLORS = {
    "treated_bamboo": {"hex": "#8B7355", "name": "Bamboo Brown"},
    "reclaimed_timber": {"hex": "#A0522D", "name": "Timber Sienna"},
    "stabilized_mud_brick": {"hex": "#CD853F", "name": "Mud Brick"},
    "corrugated_tin": {"hex": "#708090", "name": "Steel Slate"},
    "steel_connector": {"hex": "#4682B4", "name": "Steel Blue"},
}

MEMBER_TYPE_COLORS = {
    "beam": {"hex": "#4CAF50", "name": "Green"},
    "rafter": {"hex": "#FF9800", "name": "Orange"},
    "brace": {"hex": "#2196F3", "name": "Blue"},
    "column": {"hex": "#9C27B0", "name": "Purple"},
    "panel": {"hex": "#607D8B", "name": "Grey"},
}


@router.get("/generated-designs/{design_id}/geometry")
def get_geometry(design_id: int, project_id: int, site_id: int, db: Session = Depends(get_db)):
    """
    Return professional 3D scene data for a generated design.
    Computes actual 3D coordinates for all truss members.
    """
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    # Load constraint set for dimensions
    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    if cs_record is None:
        raise HTTPException(status_code=404, detail="Constraint set not found")

    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json)
    design_data = json.loads(record.design_json)

    span_m = design_data.get("span_m", constraints.site.length_m)
    height_m = design_data.get("height_m", 1.0)
    width_m = constraints.site.width_m

    # First material for default
    material_id = constraints.materials[0].id if constraints.materials else "default"
    diameter_m = constraints.materials[0].diameter_m or 0.08 if constraints.materials else 0.08

    # Count braces from the design
    members_data = design_data.get("members", [])
    brace_count = sum(1 for m in members_data if m.get("type") == "brace")

    # Build full 3D truss geometry
    truss = build_full_shelter(
        span_m=span_m,
        height_m=height_m,
        material_id=material_id,
        diameter_m=diameter_m,
        width_m=width_m,
        brace_count=max(brace_count, 1),
        wall_height_m=2.4,
    )

    truss_dict = truss.to_dict()

    # Add material colors
    material_info = {}
    for mat_type, props in MATERIAL_CATALOG.items():
        color = MATERIAL_COLORS.get(mat_type, {"hex": "#999999", "name": "Unknown"})
        material_info[mat_type] = {
            "type": mat_type,
            "display_name": props.display_name,
            "color": color,
            "unit_cost_usd": props.unit_cost_usd,
        }

    # Add member type colors
    member_type_info = {}
    for mtype, color in MEMBER_TYPE_COLORS.items():
        member_type_info[mtype] = color

    # Compute camera settings
    all_x = [p["x"] for p in truss_dict["nodes"].values()]
    all_y = [p["y"] for p in truss_dict["nodes"].values()]
    all_z = [p["z"] for p in truss_dict["nodes"].values()]

    span_x = max(all_x) - min(all_x) if all_x else 1
    span_y = max(all_y) - min(all_y) if all_y else 1
    span_z = max(all_z) - min(all_z) if all_z else 1
    max_span = max(span_x, span_y, span_z)

    return {
        "design_id": design_id,
        "candidate_id": record.candidate_id,
        "version": record.version,
        **truss_dict,
        "materials": material_info,
        "member_type_colors": member_type_info,
        "camera": {
            "position": {
                "x": round(truss_dict["center"]["x"] + max_span * 1.5, 4),
                "y": round(truss_dict["center"]["y"] + max_span * 0.8, 4),
                "z": round(truss_dict["center"]["z"] + max_span * 1.5, 4),
            },
            "target": truss_dict["center"],
            "distance": round(max_span * 2.5, 4),
            "near": 0.01,
            "far": 1000,
        },
        "grid": {
            "size": max(10, int(max_span * 2)),
            "divisions": 20,
            "color": "#444444",
        },
        "axes": {
            "length": round(max_span * 0.5, 4),
            "origin": {"x": 0, "y": 0, "z": 0},
        },
    }


@router.get("/generated-designs/{design_id}/geometry/simple")
def get_simple_geometry(design_id: int, project_id: int, site_id: int, db: Session = Depends(get_db)):
    """Return simplified single-truss geometry (front face only)."""
    record = db.get(GeneratedDesign, design_id)
    if record is None or record.site_id != site_id:
        raise HTTPException(status_code=404, detail="Generated design not found")

    cs_record = db.get(ConstraintSetRecord, record.constraint_set_id)
    if cs_record is None:
        raise HTTPException(status_code=404, detail="Constraint set not found")

    constraints = ConstraintSet.model_validate_json(cs_record.constraint_json)
    design_data = json.loads(record.design_json)

    span_m = design_data.get("span_m", constraints.site.length_m)
    height_m = design_data.get("height_m", 1.0)
    material_id = constraints.materials[0].id if constraints.materials else "default"
    diameter_m = constraints.materials[0].diameter_m or 0.08 if constraints.materials else 0.08
    members_data = design_data.get("members", [])
    brace_count = sum(1 for m in members_data if m.get("type") == "brace")

    truss = build_simple_truss(span_m, height_m, material_id, diameter_m, brace_count=max(brace_count, 1))

    truss_dict = truss.to_dict()
    truss_dict["design_id"] = design_id

    return truss_dict
