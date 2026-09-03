from pathlib import Path
from typing import BinaryIO, Protocol


class MediaStorage(Protocol):
    def save(self, file: BinaryIO, storage_key: str) -> int:
        ...

    def get_path(self, storage_key: str) -> Path:
        ...

    def exists(self, storage_key: str) -> bool:
        ...

    def delete(self, storage_key: str) -> None:
        ...
