# Step 12 — Geometry Builder

Converts the canonical Panah `DesignVersion` into structured,
renderer-independent geometry.

## Current scope
- Design type: `roof_truss`
- Member types: `beam`, `brace`

Each primitive preserves its `component_id`, `material_id`, dimensions,
position, and rotation.

## Boundary
This layer does not create Three.js meshes, export GLB/GLTF, validate safety,
or modify the canonical design. The canonical design remains the source of truth.

## Flow
Canonical DesignVersion → Geometry Builder → GeometryBuildResult
