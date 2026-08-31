# Step 13 — ConstraintSet

Implements the blueprint's canonical requirements object shared by generation
and validation.

Shape:

ConstraintSet
- schema_version
- version
- occupancy.people
- site.length_m / width_m
- materials[]
- environment.scenario
- design_target
- unknowns[]

This step is intentionally additive. It does not modify existing geometry,
DesignVersion, API, database, or frontend files. ConstraintSet is requirements
data only; it contains no generated geometry or PASS/FAIL status.

The blueprint's flow is:
ConstraintSet → AI generation → Candidate JSON → canonical DesignVersion.
The same ConstraintSet is also available to the deterministic validator.
