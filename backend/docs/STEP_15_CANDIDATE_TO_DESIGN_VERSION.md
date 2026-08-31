# Step 15 — Candidate → Canonical DesignVersion

## Purpose

Close the most important boundary after generation:

```text
ConstraintSet
    ↓
LocalGenerationService
    ↓
GenerationCandidate
    ↓
candidate_to_design_version()
    ↓
CanonicalDesignVersion
```

The canonical `DesignVersion` is the application-owned contract consumed by
geometry, validation, persistence, and review.

## Why this is separate

The generator may eventually be:

- the local deterministic generator used for the hackathon
- an Alibaba/Qwen provider
- another model provider
- a future procedural generator

None of those providers should define Panah's canonical design representation.

The converter therefore copies the candidate into the existing
`CanonicalDesignVersion` model.

## Preserved identity

The conversion preserves:

- design type
- span
- height
- component IDs
- material IDs
- member dimensions
- connections

## Boundary

This step does not:

- decide whether the design is safe
- assign PASS/FAIL
- create 3D meshes
- call an external AI provider
- mutate the original candidate

## Result

After this step the backend has a complete local path from requirements to
canonical structured design data, independent of Alibaba access.
