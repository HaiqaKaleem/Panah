from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _gps_decimal(values: Any, ref: str | None) -> float | None:
    if not values or len(values) != 3:
        return None

    parts = [_to_float(v) for v in values]
    if any(v is None for v in parts):
        return None

    result = parts[0] + parts[1] / 60 + parts[2] / 3600
    if ref in {"S", "W"}:
        result = -result
    return result


def _extract_image(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": "image"}

    with Image.open(path) as image:
        result.update({
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
        })

        exif = image.getexif()
        named: dict[str, Any] = {}

        for tag_id, value in exif.items():
            named[TAGS.get(tag_id, str(tag_id))] = _json_safe(value)

        result["exif"] = named

        gps = exif.get(34853)
        if gps:
            gps_named = {
                GPSTAGS.get(tag_id, str(tag_id)): _json_safe(value)
                for tag_id, value in gps.items()
            }
            result["gps"] = gps_named

            lat = _gps_decimal(gps.get(2), gps.get(1))
            lon = _gps_decimal(gps.get(4), gps.get(3))
            if lat is not None and lon is not None:
                result["gps_decimal"] = {
                    "latitude": lat,
                    "longitude": lon,
                }

        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            if key in named:
                result["embedded_captured_at"] = named[key]
                break

    return result


def _extract_video(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "kind": "video",
        "format": path.suffix.lower().lstrip(".") or None,
    }

    try:
        import cv2
    except ImportError:
        result["video_reader"] = "unavailable"
        return result

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        result["video_reader"] = "unavailable"
        return result

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        result["width"] = int(width) if width else None
        result["height"] = int(height) if height else None
        result["fps"] = float(fps) if fps else None

        if fps and frames:
            result["duration_seconds"] = float(frames / fps)
    finally:
        capture.release()

    return result


def extract_metadata(
    path: Path,
    mime_type: str,
    file_size: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "extractor_version": "1.0",
        "mime_type": mime_type,
        "file_size": file_size,
    }

    try:
        if mime_type.startswith("image/"):
            result["technical"] = _extract_image(path)
        elif mime_type.startswith("video/"):
            result["technical"] = _extract_video(path)
        else:
            result["technical"] = {}
            result["extraction_status"] = "unsupported"
            return result

        result["extraction_status"] = "complete"

    except Exception as exc:
        result["technical"] = {}
        result["extraction_status"] = "failed"
        result["extraction_error"] = str(exc)

    return result
