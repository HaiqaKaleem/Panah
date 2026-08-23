from collections.abc import Sequence
from app.constraints.schemas import ConstraintSet, EnvironmentConstraint, MaterialConstraint, OccupancyConstraint, SiteConstraint

def build_constraint_set(*, version: str, occupants: int, site_length_m: float, site_width_m: float,
                         materials: Sequence[MaterialConstraint | dict], environment_scenario: str,
                         design_target: str = "roof_truss", unknowns: Sequence[str] = ()) -> ConstraintSet:
    normalized = [m if isinstance(m, MaterialConstraint) else MaterialConstraint.model_validate(m) for m in materials]
    return ConstraintSet(
        version=version,
        occupancy=OccupancyConstraint(people=occupants),
        site=SiteConstraint(length_m=site_length_m, width_m=site_width_m),
        materials=normalized,
        environment=EnvironmentConstraint(scenario=environment_scenario),
        design_target=design_target,
        unknowns=list(unknowns),
    )
