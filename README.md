# Panagah API — Step 2: Site + Capture

This step adds ONLY two new concepts:

1. Site
2. Capture session

No media uploads, AI analysis, observations, materials, validation, or design generation are included yet.

## Relationship

Project
  └── Site
       └── Capture

A Site is the physical case being assessed.

A Capture is one field visit/session. Photos and videos will be attached to a Capture in the next step.

## Site endpoints

POST   /api/v1/projects/{project_id}/sites
GET    /api/v1/projects/{project_id}/sites
GET    /api/v1/projects/{project_id}/sites/{site_id}
PATCH  /api/v1/projects/{project_id}/sites/{site_id}

## Capture endpoints

POST   /api/v1/projects/{project_id}/sites/{site_id}/captures
GET    /api/v1/projects/{project_id}/sites/{site_id}/captures
GET    /api/v1/projects/{project_id}/sites/{site_id}/captures/{capture_id}

## Important design choice

A Site does NOT contain photos/videos directly.

The structure is:

Project → Site → Capture → Media

This preserves the context of each field visit and lets the same site have multiple assessment sessions.

## Current Site fields

- id
- project_id
- name
- latitude (optional)
- longitude (optional)
- status
- created_at
- updated_at

## Current Capture fields

- id
- site_id
- captured_at
- latitude (optional)
- longitude (optional)
- status
- notes (optional)
- created_at

## Not implemented yet

- file upload/storage
- photo/video records
- thumbnails
- AI/CV analysis
- detected objects
- site observations
- human confirmation
- measurements
- material inventory

Those are deliberately separate next steps.


## Step 5 — Metadata Extraction

Media now receives a technical/embedded metadata extraction pass after upload.

### Images
- width / height
- format / mode
- EXIF fields
- EXIF GPS when present
- embedded capture timestamp when present

### Videos
- format
- dimensions / FPS / duration when an optional video reader is available

### Design guarantees
- original file is never modified
- extracted metadata is stored separately
- failed extraction does not invalidate the evidence file
- metadata extraction does not perform AI interpretation


## Step 7 — Site Profile

The Site Profile is the controlled bridge between visual observations and design generation.

It contains coordinator-reviewed site information:
- terrain
- visible objects/obstructions
- access
- available materials
- visible conditions
- geometry/measurements

AI observations are not automatically treated as final site facts.

Profile lifecycle:
draft -> ready

A ready profile is the input contract for the future design-generation layer.


## Step 8 — Design Specification

The Design Specification is the structured design request given to the future design generator.

It is intentionally separate from the Site Profile:

- Site Profile = what is known about the site.
- Design Specification = what the coordinator wants designed.

Current fields:
- family size
- shelter type
- required spaces
- maximum footprint
- maximum height
- available materials
- preferred materials
- design priorities
- coordinator notes

Lifecycle:
draft -> ready

Editing a ready specification automatically returns it to draft.

The schema intentionally excludes structural safety, load capacity, wind resistance,
material strength, and engineering approval. Those belong to later validation/review layers.


## Step 9 — Design Generation Contract

This step defines the output contract for a generated shelter candidate without implementing
a real 3D/AI generator.

Pipeline:

Ready Site Profile
    +
Ready Design Specification
    ↓
Design Generator
    ↓
Validated Candidate Contract
    ↓
Stored Design Candidate
    ↓
Future deterministic validation

A candidate contains:
- candidate name
- footprint
- overall height
- components
- component types
- material labels
- 3D position
- component dimensions
- generation notes

Each candidate also stores an immutable input snapshot of the Site Profile and Design
Specification used to create it. This makes generation reproducible and auditable.

The current generator is a deterministic local mock/parametric generator. It is NOT AI
and it does NOT perform structural validation or claim safety.

The contract intentionally separates:
- generation
- validation
- engineer approval

A future AI/optimization provider can replace the mock generator without changing the API
or database contract.
