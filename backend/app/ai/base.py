from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AIObservation:
    observation_type: str
    label: str
    confidence: float
    bbox_x: float | None = None
    bbox_y: float | None = None
    bbox_width: float | None = None
    bbox_height: float | None = None
    evidence_timestamp_seconds: float | None = None
    analysis_metadata: dict | None = None

class SiteVisionProvider(Protocol):
    def analyze_media(self, file_path: str, mime_type: str) -> list[AIObservation]:
        ...
