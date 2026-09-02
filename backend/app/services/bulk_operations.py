"""Bulk import/export service — CSV, JSON, and structured data operations."""

import csv
import io
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/bulk", tags=["Bulk Operations"])


class BulkExporter:
    """Export data in multiple formats."""

    @staticmethod
    def to_csv(data: list[dict], filename: str = "export.csv") -> StreamingResponse:
        """Export list of dicts to CSV."""
        if not data:
            data = [{}]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @staticmethod
    def to_json(data: list[dict], filename: str = "export.json",
                pretty: bool = True) -> StreamingResponse:
        """Export list of dicts to JSON."""
        content = json.dumps(data, indent=2 if pretty else None, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @staticmethod
    def to_jsonl(data: list[dict], filename: str = "export.jsonl") -> StreamingResponse:
        """Export list of dicts to JSON Lines (NDJSON)."""
        lines = "\n".join(json.dumps(record, default=str) for record in data)
        return StreamingResponse(
            iter([lines]),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


class BulkImporter:
    """Import data from multiple formats."""

    @staticmethod
    def from_csv(content: str) -> list[dict]:
        """Parse CSV content to list of dicts."""
        reader = csv.DictReader(io.StringIO(content))
        return [dict(row) for row in reader]

    @staticmethod
    def from_json(content: str) -> list[dict]:
        """Parse JSON content to list of dicts."""
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]

    @staticmethod
    def from_jsonl(content: str) -> list[dict]:
        """Parse JSON Lines to list of dicts."""
        return [json.loads(line) for line in content.strip().split("\n") if line.strip()]


exporter = BulkExporter()
importer = BulkImporter()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.post("/export/{entity_type}", summary="Export entities to CSV/JSON")
async def export_entities(
    entity_type: str,
    format: str = Query("json", pattern="^(csv|json|jsonl)$"),
    project_id: Optional[str] = None,
):
    """
    Export entities in bulk.

    - **entity_type**: projects, sites, materials, designs, constraints
    - **format**: csv, json, or jsonl
    - **project_id**: Optional filter by project
    """
    # Sample data generation (in production, query from DB)
    sample_data = _get_sample_export(entity_type, project_id)

    if format == "csv":
        return exporter.to_csv(sample_data, f"{entity_type}_export.csv")
    elif format == "jsonl":
        return exporter.to_jsonl(sample_data, f"{entity_type}_export.jsonl")
    else:
        return exporter.to_json(sample_data, f"{entity_type}_export.json")


@router.post("/import/{entity_type}", summary="Import entities from CSV/JSON")
async def import_entities(
    entity_type: str,
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    dry_run: bool = Query(False, description="Validate without saving"),
):
    """
    Import entities from uploaded file.

    - **file**: CSV, JSON, or JSONL file
    - **project_id**: Assign all imported entities to this project
    - **dry_run**: Validate data without persisting
    """
    content = (await file.read()).decode("utf-8")

    # Detect format
    filename = file.filename or ""
    if filename.endswith(".csv"):
        records = importer.from_csv(content)
    elif filename.endswith(".jsonl"):
        records = importer.from_jsonl(content)
    else:
        records = importer.from_json(content)

    # Validate
    valid = []
    errors = []
    for i, record in enumerate(records):
        is_valid, error = _validate_import_record(entity_type, record)
        if is_valid:
            record["id"] = str(uuid.uuid4())[:12]
            record["imported_at"] = datetime.utcnow().isoformat()
            if project_id:
                record["project_id"] = project_id
            valid.append(record)
        else:
            errors.append({"row": i + 1, "error": error, "data": record})

    result = {
        "total_rows": len(records),
        "valid_rows": len(valid),
        "error_rows": len(errors),
        "errors": errors[:50],  # Limit error output
    }

    if not dry_run:
        # In production: bulk insert to DB
        result["imported"] = len(valid)
        result["status"] = "completed"
    else:
        result["status"] = "dry_run"
        result["message"] = "Data validated. Set dry_run=false to import."

    return result


@router.get("/templates/{entity_type}", summary="Download CSV import template")
async def download_template(entity_type: str):
    """Download a CSV template for bulk import."""
    templates = {
        "projects": [
            {"name": "Example Project", "description": "Emergency shelter assessment"}
        ],
        "sites": [
            {"name": "Site Alpha", "latitude": "33.69", "longitude": "73.05"}
        ],
        "materials": [
            {"name": "Guadua Bamboo", "material_type": "bamboo", "quantity": "100",
             "unit": "pieces", "unit_cost": "15.00"}
        ],
        "designs": [
            {"name": "Candidate A", "status": "pending"}
        ],
        "constraints": [
            {"name": "Emergency Constraints", "schema_version": "1.0"}
        ],
    }

    data = templates.get(entity_type, [{"field": "value"}])
    return exporter.to_csv(data, f"{entity_type}_template.csv")


def _get_sample_export(entity_type: str, project_id: Optional[str]) -> list[dict]:
    """Get sample data for export (replace with DB query in production)."""
    if entity_type == "projects":
        return [
            {"id": "prj_001", "name": "Camp Alpha", "description": "Emergency shelter", "version": "0.1.0"},
            {"id": "prj_002", "name": "Camp Beta", "description": "Transitional housing", "version": "0.2.0"},
        ]
    elif entity_type == "materials":
        return [
            {"id": "mat_001", "name": "Guadua Bamboo", "type": "bamboo", "quantity": 100, "unit": "pieces"},
            {"id": "mat_002", "name": "Stabilized Mud-Brick", "type": "earth", "quantity": 500, "unit": "bricks"},
        ]
    return []


def _validate_import_record(entity_type: str, record: dict) -> tuple[bool, str]:
    """Validate a single import record."""
    if entity_type == "projects":
        if not record.get("name"):
            return False, "Missing required field: name"
    elif entity_type == "materials":
        if not record.get("name"):
            return False, "Missing required field: name"
        if not record.get("material_type"):
            return False, "Missing required field: material_type"
    elif entity_type == "sites":
        if not record.get("name"):
            return False, "Missing required field: name"
    return True, ""
