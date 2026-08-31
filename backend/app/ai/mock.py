from app.ai.base import AIObservation

class MockVisionProvider:
    """Development-only synthetic provider; not real AI."""
    def analyze_media(self, file_path, mime_type):
        return [AIObservation(
            observation_type="terrain",
            label="uneven_ground",
            confidence=0.82,
            analysis_metadata={
                "provider": "mock",
                "synthetic": True,
                "warning": "development-only synthetic observation"
            }
        )]
