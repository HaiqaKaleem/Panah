from pathlib import Path
from typing import BinaryIO


class LocalMediaStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _safe_path(self, storage_key: str) -> Path:
        relative = Path(storage_key)

        # Storage keys must be relative and must never escape the storage root.
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid storage key")

        path = (self.root / relative).resolve()

        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Invalid storage key") from exc

        return path

    def save(self, file: BinaryIO, storage_key: str) -> int:
        destination = self._safe_path(storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)

        total = 0
        with destination.open("wb") as output:
            while chunk := file.read(1024 * 1024):
                output.write(chunk)
                total += len(chunk)

        return total

    def get_path(self, storage_key: str) -> Path:
        path = self._safe_path(storage_key)

        if not path.exists():
            raise FileNotFoundError(storage_key)

        return path

    def exists(self, storage_key: str) -> bool:
        return self._safe_path(storage_key).exists()

    def delete(self, storage_key: str) -> None:
        path = self._safe_path(storage_key)

        if path.exists():
            path.unlink()
