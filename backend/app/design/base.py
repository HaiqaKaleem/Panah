from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationInput:
    site_profile: dict
    design_specification: dict


class DesignGenerator(Protocol):
    name: str
    version: str

    def generate(
        self,
        generation_input: GenerationInput,
    ) -> dict:
        ...
