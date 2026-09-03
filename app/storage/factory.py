from pathlib import Path

from app.storage.local import LocalMediaStorage


def get_media_storage() -> LocalMediaStorage:
    return LocalMediaStorage(Path("storage/media"))
