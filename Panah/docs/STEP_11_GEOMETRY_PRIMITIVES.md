# Step 11 — Parametric Geometry Primitives

This step introduces the first geometry layer for Panah.

## Purpose

The canonical `DesignVersion` remains the source of truth. The geometry layer converts
its members into renderer-independent geometric primitives.

Current supported primitives:

- beam
- brace
- panel (schema-supported; builder support can be added when the canonical design
  contains panel members)

## Boundary

This step does **not**:

- generate arbitrary AI meshes
- create Three.js objects
- export GLB/GLTF
- perform structural validation
- decide whether a design is safe

The flow is:

Canonical DesignVersion → Geometry Builder → Structured Geometry Primitives

Every primitive preserves:

- component ID
- material ID
- dimensions
- position
- rotation

This allows a future renderer and validator to refer to the same physical component.
