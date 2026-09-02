
from pathlib import Path

from app.metadata.extractor import extract_metadata


def test_unknown_type_is_unsupported(tmp_path):
    path = tmp_path / "panagah_unknown.bin"
    path.write_bytes(b"anything")

    result = extract_metadata(
        path,
        "application/octet-stream",
        8,
    )

    assert result["extraction_status"] == "unsupported"
    assert result["technical"] == {}


def test_corrupt_image_returns_failed_result(tmp_path):
    path = tmp_path / "panagah_corrupt.jpg"
    path.write_bytes(b"corrupt")

    result = extract_metadata(
        path,
        "image/jpeg",
        7,
    )

    assert result["extraction_status"] == "failed"
    assert "extraction_error" in result