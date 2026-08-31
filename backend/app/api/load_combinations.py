"""Load Combination Generator API — ASCE 7-style load combinations for structural design."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/load-combinations", tags=["Structural Loads"])


class LoadCombination(BaseModel):
    name: str
    factors: dict[str, float]
    description: str
    category: str  # strength, serviceability, seismic, wind


# Standard ASCE 7-16 load combinations (simplified for shelter design)
SHELTER_LOAD_COMBINATIONS: list[LoadCombination] = [
    LoadCombination(
        name="LC-1",
        factors={"dead": 1.4},
        description="Dead load only",
        category="strength",
    ),
    LoadCombination(
        name="LC-2",
        factors={"dead": 1.2, "live": 1.6},
        description="Dead + Live load",
        category="strength",
    ),
    LoadCombination(
        name="LC-3",
        factors={"dead": 1.2, "live": 1.0, "wind": 1.0},
        description="Dead + Live + Wind (low wind)",
        category="strength",
    ),
    LoadCombination(
        name="LC-4",
        factors={"dead": 0.9, "wind": 1.0},
        description="Dead (reduced) + Wind (overturning check)",
        category="wind",
    ),
    LoadCombination(
        name="LC-5",
        factors={"dead": 1.2, "snow": 1.6},
        description="Dead + Snow load",
        category="strength",
    ),
    LoadCombination(
        name="LC-6",
        factors={"dead": 1.2, "snow": 0.5, "wind": 1.0},
        description="Dead + Snow (reduced) + Wind",
        category="strength",
    ),
    LoadCombination(
        name="LC-7",
        factors={"dead": 1.0, "live": 1.0},
        description="Dead + Live (serviceability — deflection check)",
        category="serviceability",
    ),
    LoadCombination(
        name="LC-8",
        factors={"dead": 1.0, "snow": 1.0},
        description="Dead + Snow (serviceability — deflection check)",
        category="serviceability",
    ),
    LoadCombination(
        name="LC-9",
        factors={"dead": 1.2, "seismic": 1.0, "live": 0.5},
        description="Dead + Seismic + Live (reduced)",
        category="seismic",
    ),
]


@router.get("")
def list_load_combinations(category: str | None = None):
    """
    Return standard load combinations for shelter structural design.
    Filter by category: strength, serviceability, wind, seismic.
    """
    combos = SHELTER_LOAD_COMBINATIONS
    if category:
        combos = [c for c in combos if c.category == category]

    return {
        "standard": "ASCE 7-16 (simplified for shelter design)",
        "count": len(combos),
        "combinations": [c.model_dump() for c in combos],
    }


@router.get("/categories")
def list_combination_categories():
    """Return available load combination categories."""
    categories = sorted(set(c.category for c in SHELTER_LOAD_COMBINATIONS))
    return {
        "categories": [
            {
                "name": cat,
                "count": sum(1 for c in SHELTER_LOAD_COMBINATIONS if c.category == cat),
            }
            for cat in categories
        ]
    }


@router.get("/governing")
def get_governing_combination():
    """
    Return the governing (most critical) load combination for a simple shelter.
    For emergency shelters, wind uplift (LC-4) or snow (LC-5) typically governs.
    """
    return {
        "governing": SHELTER_LOAD_COMBINATIONS[3].model_dump(),  # LC-4: wind uplift
        "reason": "Wind uplift governs for lightweight emergency shelters — dead load reduction is critical when resisting overturning.",
        "recommendation": "Verify overturning resistance under LC-4. Cross-bracing must resist lateral wind forces per Sphere standard.",
    }
