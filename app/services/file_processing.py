"""File processing pipeline — image analysis, EXIF extraction, format conversion, and validation."""

import hashlib
import io
import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/files", tags=["File Processing"])


class ImageAnalyzer:
    """Analyze uploaded images for metadata, quality, and content."""

    def __init__(self):
        self._processed_count = 0

    async def analyze(self, file: UploadFile) -> dict:
        """Analyze an uploaded image file."""
        content = await file.read()
        self._processed_count += 1

        # Basic analysis
        file_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        result = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": file_size,
            "size_human": self._human_size(file_size),
            "hash_sha256": file_hash,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        # Image-specific analysis
        if file.content_type and file.content_type.startswith("image/"):
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(content))
                result["dimensions"] = {
                    "width": img.width,
                    "height": img.height,
                    "megapixels": round(img.width * img.height / 1_000_000, 2),
                }
                result["format"] = img.format
                result["mode"] = img.mode

                # EXIF data
                if hasattr(img, "_getexif") and img._getexif():
                    exif = img._getexif()
                    result["exif"] = {
                        k: str(v) for k, v in list(exif.items())[:20]  # Limit to 20 fields
                    }

                # Quality assessment
                result["quality"] = self._assess_quality(img, file_size)

            except Exception as e:
                result["analysis_error"] = str(e)

        return result

    def _assess_quality(self, img, file_size: int) -> dict:
        """Assess image quality for field documentation."""
        megapixels = img.width * img.height / 1_000_000
        aspect_ratio = img.width / img.height

        # Resolution rating
        if megapixels >= 12:
            resolution = "excellent"
        elif megapixels >= 8:
            resolution = "good"
        elif megapixels >= 4:
            resolution = "acceptable"
        else:
            resolution = "low"

        # File size efficiency
        bytes_per_pixel = file_size / (img.width * img.height)
        efficiency = "optimal" if bytes_per_pixel < 1 else "large" if bytes_per_pixel < 3 else "very_large"

        return {
            "resolution": resolution,
            "megapixels": round(megapixels, 2),
            "aspect_ratio": round(aspect_ratio, 2),
            "file_efficiency": efficiency,
            "suitable_for_documentation": megapixels >= 2 and file_size < 10_000_000,
        }

    def _human_size(self, size: int) -> str:
        """Convert bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {"total_processed": self._processed_count}


class FileValidator:
    """Validate uploaded files against allowed types and size limits."""

    ALLOWED_TYPES = {
        "image": {"extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
                  "max_size_mb": 20, "content_types": ["image/"]},
        "document": {"extensions": [".pdf", ".doc", ".docx", ".txt"],
                     "max_size_mb": 50, "content_types": ["application/pdf", "text/"]},
        "data": {"extensions": [".csv", ".json", ".jsonl", ".xlsx"],
                 "max_size_mb": 10, "content_types": ["text/", "application/json", "application/csv"]},
        "3d_model": {"extensions": [".gltf", ".glb", ".obj", ".ifc", ".stl"],
                     "max_size_mb": 100, "content_types": ["model/", "application/octet-stream"]},
    }

    def validate(self, filename: str, content_type: str, size: int,
                 category: Optional[str] = None) -> dict:
        """Validate a file against type and size constraints."""
        ext = os.path.splitext(filename)[1].lower()
        errors = []

        # Find matching category
        matched_category = None
        for cat_name, cat_config in self.ALLOWED_TYPES.items():
            if category and cat_name != category:
                continue
            if ext in cat_config["extensions"]:
                matched_category = cat_name
                # Check size
                max_bytes = cat_config["max_size_mb"] * 1024 * 1024
                if size > max_bytes:
                    errors.append(f"File too large: {size / 1024 / 1024:.1f}MB > {cat_config['max_size_mb']}MB limit")
                break

        if not matched_category and not errors:
            errors.append(f"Unsupported file type: {ext}")

        return {
            "valid": len(errors) == 0,
            "filename": filename,
            "extension": ext,
            "category": matched_category,
            "errors": errors,
        }


class FormatConverter:
    """Convert files between formats."""

    @staticmethod
    def json_to_csv(data: list[dict]) -> str:
        """Convert JSON data to CSV format."""
        if not data:
            return ""

        import csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def csv_to_json(content: str) -> list[dict]:
        """Convert CSV content to JSON format."""
        import csv
        reader = csv.DictReader(io.StringIO(content))
        return [dict(row) for row in reader]

    @staticmethod
    def json_to_jsonl(data: list[dict]) -> str:
        """Convert JSON array to JSON Lines."""
        return "\n".join(json.dumps(record, default=str) for record in data)

    @staticmethod
    def jsonl_to_json(content: str) -> list[dict]:
        """Convert JSON Lines to JSON array."""
        return [json.loads(line) for line in content.strip().split("\n") if line.strip()]


# Global instances
image_analyzer = ImageAnalyzer()
file_validator = FileValidator()
format_converter = FormatConverter()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.post("/analyze", summary="Analyze uploaded file")
async def analyze_file(file: UploadFile = File(...)):
    """
    Analyze an uploaded file. Returns:
    - File metadata (size, hash, type)
    - Image dimensions and quality (for images)
    - EXIF data (if available)
    - Quality assessment
    """
    return await image_analyzer.analyze(file)


@router.post("/validate", summary="Validate file against constraints")
async def validate_file(file: UploadFile = File(...),
                        category: Optional[str] = Query(None)):
    """
    Validate a file against type and size constraints.

    Categories: image, document, data, 3d_model
    """
    content = await file.read()
    return file_validator.validate(
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        category=category,
    )


@router.post("/convert", summary="Convert file between formats")
async def convert_file(source_format: str, target_format: str,
                       data: list[dict]):
    """
    Convert data between formats.

    Supported conversions:
    - json -> csv, jsonl
    - csv -> json
    - jsonl -> json
    """
    if source_format == "json" and target_format == "csv":
        csv_content = format_converter.json_to_csv(data)
        return {"format": "csv", "content": csv_content}
    elif source_format == "csv" and target_format == "json":
        # Assume data is a list with single CSV content string
        json_data = format_converter.csv_to_json(data[0].get("content", "") if data else "")
        return {"format": "json", "data": json_data}
    elif source_format == "json" and target_format == "jsonl":
        jsonl_content = format_converter.json_to_jsonl(data)
        return {"format": "jsonl", "content": jsonl_content}
    elif source_format == "jsonl" and target_format == "json":
        json_data = format_converter.jsonl_to_json(data[0].get("content", "") if data else "")
        return {"format": "json", "data": json_data}
    else:
        return {"error": f"Unsupported conversion: {source_format} -> {target_format}"}


@router.get("/stats", summary="File processing statistics")
async def file_stats():
    """Get file processing statistics."""
    return image_analyzer.get_stats()


@router.get("/allowed-types", summary="List allowed file types")
async def allowed_types():
    """Get all allowed file types and their constraints."""
    return file_validator.ALLOWED_TYPES
