# Panagah (پناگاہ) — Humanitarian Shelter Assessment & Design Platform

> **Constraint-driven generative design for humanitarian shelter assessment**
>
> A production-grade FastAPI backend that collects field requirements, converts them into canonical constraint models, generates structured shelter-component candidates, builds parametric 3D geometry, and independently evaluates designs through a deterministic validation engine — all before presenting evidence to a human engineer.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-417-passing-brightgreen?style=flat-square)
![Endpoints](https://img.shields.io/badge/Endpoints-115+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Engineering Modules](#engineering-modules)
- [Validation Engine](#validation-engine)
- [Platform Services](#platform-services)
- [3D Viewer](#3d-viewer)
- [Testing](#testing)
- [Deployment](#deployment)
- [UI Screenshots](#ui-screenshots)
- [Contributing](#contributing)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PANAGAH ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ Frontend │───▶│ FastAPI  │───▶│SQLAlchemy│───▶│ Database │      │
│  │  (Next.js)│   │  Router  │    │  Models  │    │(SQLite/PG)│     │
│  └──────────┘    └────┬─────┘    └──────────┘    └──────────┘      │
│                       │                                             │
│          ┌────────────┼────────────┐                               │
│          ▼            ▼            ▼                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │Generator │  │Validator │  │Engineering│                         │
│  │ Service  │  │  Engine  │  │  Modules  │                         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                         │
│       │              │              │                               │
│       ▼              ▼              ▼                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │ Geometry │  │  YAML    │  │  PDF     │                         │
│  │ Builder  │  │  Rules   │  │ Reports  │                         │
│  └────┬─────┘  └──────────┘  └──────────┘                         │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                       │
│  │ Three.js │  (docs/viewer3d.html)                                │
│  │ 3D Viewer│                                                       │
│  └──────────┘                                                       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Platform Services: Job Queue │ Webhooks │ API Keys │ Cache │ Audit │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Project ──▶ Site ──▶ Capture ──▶ Media ──▶ Observations / AI Analysis
         ──▶ SiteProfile (draft→ready) + DesignSpecification (draft→ready)
         ──▶ ConstraintSet
              ──▶ DesignGenerator ──▶ DesignCandidate ──▶ DesignVersion
              ──▶ LocalGenerationService ──▶ GenerationCandidate
         ──▶ DesignVersion
              ──▶ StructuralAnalysis ──▶ Findings
              ──▶ GeometryBuilder ──▶ Primitives (3D)
              ──▶ Validation ──▶ EngineerReview
              ──▶ BOM ──▶ Cost Estimation
              ──▶ PDF Report
```

### Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Safety separation** | Generation never claims engineering safety; analysis, standards, and compliance are separate layers |
| **Provider protocols** | AI and design generators use Protocol classes with mock implementations for MVP |
| **Deterministic prescreening** | Rules use `NOT_EVALUATED` for missing evidence — never fake a pass |
| **Schema strictness** | All Pydantic models use `extra="forbid"` to reject unexpected fields |
| **Content deduplication** | SHA-256 prevents duplicate uploads to same capture |
| **Path traversal protection** | Storage keys validated to never escape root |
| **Immutable versioning** | Design versions are immutable once created — all changes produce new versions |
| **Audit trail** | Every significant action is logged with actor, timestamp, and metadata |

---

## Features

### Core Pipeline
- **Constraint-driven generation** — Form data → canonical constraint models → AI/mock generation
- **Parametric 3D geometry** — Truss builder with king post, diagonal braces, ridge beams, wall columns
- **Deterministic validation** — YAML rule engine with 8 Sphere Handbook rules
- **Engineer review workflow** — Submit → review → decision → immutable audit trail

### Engineering Calculations
| Module | Description |
|--------|-------------|
| **Wind Load (ASCE 7-22)** | 6-zone pressure calculation for low-rise shelters, velocity pressure, gust factor |
| **Seismic Load (ELF)** | Base shear + vertical distribution, 9 South Asia seismic zones, 5 soil classes |
| **Pareto Optimization** | Multi-objective design ranking with non-dominated sorting |
| **Safety Factors** | Per-member axial/bending/shear capacity vs demand analysis |
| **Cost Estimation** | Material + labor + transport + contingency, 4-region labor rates |
| **Material Substitution** | Compatibility scoring, availability, cost comparison |
| **Design Diff** | Structured member-level comparison between two designs |
| **Report Generator** | Professional 7-section PDF engineering report |
| **Geo-Climate Lookup** | 6 climate zones with hazard profiles and material recommendations |
| **3D Model Export** | glTF 2.0, IFC (BIM), OBJ mesh formats |

### Platform Services
| Service | Description |
|---------|-------------|
| **Background Job Queue** | Priority levels, retry logic, progress tracking |
| **API Key Management** | 3 tiers (free/pro/enterprise), key generation and revocation |
| **Rate Limiting** | Sliding window rate limiter per API key tier |
| **Webhook System** | Event-driven notifications with HMAC signatures and delivery tracking |
| **In-Memory Cache** | TTL-based caching with namespace scoping and LRU eviction |
| **Audit Trail** | Event logging for all significant actions |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+ / FastAPI / Uvicorn |
| **ORM** | SQLAlchemy 2.0 (async-ready) |
| **Validation** | Pydantic v2 with strict mode |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **3D Viewer** | Three.js (standalone HTML) |
| **PDF Generation** | fpdf2 |
| **AI Provider** | Mock provider (MVP) / Alibaba Cloud Qwen (production) |
| **Storage** | Local filesystem (MVP) / Alibaba Cloud OSS (production) |
| **Testing** | pytest + httpx (417 tests) |

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/HaiqaKaleem/Panah.git
cd Panah

# Create virtual environment
python -m venv .venv

# Activate
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API available at:** `http://localhost:8000`
**Swagger docs:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

### Run Tests

```bash
# Full suite
python -m pytest tests/ -v

# Quick check
python -m pytest tests/ -q --no-header

# Specific module
python -m pytest tests/test_engineering.py -v
```

### Open 3D Viewer

```bash
# Windows
start docs/viewer3d.html

# macOS
open docs/viewer3d.html

# Linux
xdg-open docs/viewer3d.html
```

---

## Project Structure

```
Panah/
├── app/
│   ├── api/                    # FastAPI routers (115+ endpoints)
│   │   ├── projects.py         # CRUD + stats
│   │   ├── sites.py            # Site management + status transitions
│   │   ├── media.py            # Photo/video upload, dedup, serving
│   │   ├── observations.py     # Field observations + confirmation
│   │   ├── analysis.py         # AI analysis triggers
│   │   ├── site_profiles.py    # Draft/ready workflow
│   │   ├── design_specifications.py
│   │   ├── constraint_sets.py  # Builder + validator integration
│   │   ├── design_candidates.py # Generation + selection
│   │   ├── design_versions.py  # Immutable versioning
│   │   ├── generated_designs.py
│   │   ├── generated_validation.py
│   │   ├── validation.py       # Run + retrieve validations
│   │   ├── design_validation.py # YAML rule engine endpoints
│   │   ├── reviews.py          # Engineer review workflow
│   │   ├── standards.py        # Standards rules catalog
│   │   ├── load_combinations.py # ASCE 7 load combos
│   │   ├── materials.py        # Material CRUD
│   │   ├── material_catalog.py # Material types + properties
│   │   ├── materials_summary.py
│   │   ├── bom.py              # Bill of Materials
│   │   ├── comparison.py       # Design comparison matrix
│   │   ├── geometry.py         # 3D geometry endpoint
│   │   ├── export.py           # Design export (JSON)
│   │   ├── engineering.py      # Engineering calculations (10 endpoints)
│   │   ├── platform.py         # Jobs, webhooks, API keys, cache, geo-climate, export
│   │   ├── dashboard.py        # Dashboard stats
│   │   ├── project_history.py  # Project timeline
│   │   ├── audit.py            # Audit event log
│   │   ├── activity.py         # Activity feed
│   │   └── notifications.py    # Notification center
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── project.py          # Project
│   │   ├── site.py             # Site + status enum
│   │   ├── capture.py          # Capture session
│   │   ├── media.py            # Media files + SHA-256 dedup
│   │   ├── observation.py      # Field observations
│   │   ├── analysis.py         # AI analysis results
│   │   ├── material.py         # Materials
│   │   ├── design_candidate.py # Generated candidates
│   │   ├── design_version.py   # Immutable versions
│   │   ├── generated_design.py # Full generated designs
│   │   ├── validation.py       # Validation runs + results
│   │   ├── review.py           # Engineer reviews
│   │   ├── audit.py            # Audit events
│   │   ├── constraint_set.py   # Constraint sets
│   │   └── design_snapshot.py  # Design iteration snapshots
│   │
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── project.py          # ProjectCreate, ProjectResponse
│   │   ├── site.py             # SiteCreate, SiteResponse
│   │   ├── material.py         # MaterialCreate, MaterialResponse
│   │   ├── constraint_set.py   # ConstraintSet schemas
│   │   ├── design_candidate.py
│   │   ├── design_version.py
│   │   ├── review.py
│   │   ├── validation.py
│   │   └── ...
│   │
│   ├── ai/                     # AI vision provider
│   │   ├── base.py             # SiteVisionProvider protocol
│   │   ├── mock.py             # Mock provider for MVP
│   │   └── factory.py          # Provider factory
│   │
│   ├── analysis/               # Structural analysis
│   │   ├── service.py          # Analysis service
│   │   └── schemas.py          # Analysis schemas
│   │
│   ├── compliance/             # Compliance reporting
│   │   └── service.py          # Sphere Handbook compliance
│   │
│   ├── constraints/            # Constraint system
│   │   ├── builder.py          # Form → ConstraintSet
│   │   ├── validator.py        # ConstraintSet validation
│   │   └── schemas.py          # All constraint schemas
│   │
│   ├── engineering/            # Engineering calculations (NEW)
│   │   ├── wind_load.py        # ASCE 7-22 §28.3 wind pressure
│   │   ├── seismic_load.py     # ELF base shear + distribution
│   │   ├── optimization.py     # Pareto multi-objective optimization
│   │   ├── cost_estimation.py  # Detailed cost breakdown
│   │   ├── report_generator.py # PDF engineering report
│   │   ├── templates.py        # 5 pre-built shelter templates
│   │   ├── design_diff.py      # Structured design comparison
│   │   ├── material_substitution.py # Alternative materials
│   │   ├── safety_factors.py   # Per-member structural safety
│   │   ├── geo_climate.py      # Climate zone lookup
│   │   └── model_export.py     # glTF / IFC / OBJ export
│   │
│   ├── generator/              # Design generation
│   │   ├── service.py          # Local generation service
│   │   ├── converter.py        # Candidate → design version
│   │   └── schemas.py          # Generation schemas
│   │
│   ├── geometry/               # 3D geometry
│   │   ├── primitives.py       # Beam, Panel, Connector, Brace
│   │   ├── builder.py          # Geometry builder
│   │   └── truss_builder.py    # Full shelter truss generation
│   │
│   ├── services/               # Platform services (NEW)
│   │   ├── job_queue.py        # Background job queue
│   │   ├── api_keys.py         # API key management + rate limiting
│   │   ├── webhooks.py         # Event webhook system
│   │   ├── cache.py            # In-memory TTL cache
│   │   ├── audit.py            # Audit event service
│   │   ├── notifications.py    # Notification service
│   │   └── design_versions.py  # Version management
│   │
│   ├── structural/             # Structural analysis
│   │   └── analysis.py         # Load path + member analysis
│   │
│   ├── validator/              # Deterministic validation engine (NEW)
│   │   ├── engine.py           # YAML rule engine (10 methods)
│   │   ├── context.py          # ValidationContext builder
│   │   ├── result.py           # RuleResult + ValidationReport
│   │   └── rules/              # YAML rule registry
│   │       ├── r-geo-001.yaml  # Span ≤ site length
│   │       ├── r-geo-002.yaml  # Member ≤ 6m stock
│   │       ├── r-geo-003.yaml  # Clearance ≥ 2.0m
│   │       ├── r-mat-001.yaml  # At least 1 material
│   │       ├── r-mat-002.yaml  # Material in catalog
│   │       ├── r-load-001.yaml # Load path defined
│   │       ├── r-env-001.yaml  # Scenario defined
│   │       └── r-conn-001.yaml # Connections defined
│   │
│   ├── core/                   # Configuration
│   │   ├── config.py           # Settings
│   │   └── database.py         # Engine + session
│   │
│   ├── storage/                # File storage
│   │   ├── base.py             # Storage protocol
│   │   └── local.py            # Local filesystem
│   │
│   ├── metadata/               # EXIF/GPS extraction
│   └── design/                 # Design generator protocol
│
├── docs/                       # Documentation + viewer
│   ├── viewer3d.html           # Three.js 3D workspace viewer
│   ├── app.html                # Screenshot viewer
│   ├── blueprint.txt           # Implementation blueprint
│   └── screenshots/            # UI screenshots
│
├── tests/                      # Test suite (417 tests)
│   ├── test_e2e_pipeline.py    # End-to-end pipeline
│   ├── test_engineering.py     # Engineering modules (40 tests)
│   ├── test_platform.py        # Platform services (36 tests)
│   ├── test_validator_engine.py # YAML rule engine (24 tests)
│   ├── test_structural_analysis.py
│   ├── test_analysis_service.py
│   ├── test_compliance_service.py
│   ├── test_constraint_set_pipeline.py
│   └── ...
│
├── requirements.txt
└── README.md
```

---

## API Reference

All endpoints are prefixed with `/api/v1`. Total: **115+ endpoints across 30 routers**.

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects` | Create a new project |
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}` | Get project by ID |
| `PATCH` | `/projects/{id}` | Update project |
| `DELETE` | `/projects/{id}` | Delete project |
| `GET` | `/projects/{id}/stats` | Project statistics |

### Sites

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects/{pid}/sites` | Create a site |
| `GET` | `/projects/{pid}/sites` | List sites |
| `GET` | `/projects/{pid}/sites/{sid}` | Get site |
| `PATCH` | `/projects/{pid}/sites/{sid}` | Update site |
| `POST` | `/projects/{pid}/sites/{sid}/submit` | Submit for review |
| `GET` | `/projects/{pid}/sites/{sid}/compliance` | Compliance status |

### Media & Observations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `.../captures/{cid}/media` | Upload photo/video |
| `GET` | `.../captures/{cid}/media` | List media |
| `GET` | `.../media/{mid}/file` | Serve original file |
| `POST` | `.../media/{mid}/observations` | Create observation |
| `GET` | `.../media/{mid}/observations` | List observations |
| `PATCH` | `.../observations/{oid}/status` | Confirm/reject |

### AI Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `.../media/{mid}/analyze` | Run AI vision analysis |

### Requirements (Site Profiles & Design Specs)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `.../sites/{sid}/profile` | Get site profile |
| `PUT` | `.../sites/{sid}/profile` | Save site profile |
| `POST` | `.../sites/{sid}/profile/ready` | Mark profile ready |
| `GET` | `.../sites/{sid}/design-specification` | Get design spec |
| `PUT` | `.../sites/{sid}/design-specification` | Save design spec |
| `POST` | `.../sites/{sid}/design-specification/ready` | Mark spec ready |

### Constraint Sets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `.../sites/{sid}/constraint-sets` | Create constraint set |
| `GET` | `.../sites/{sid}/constraint-sets` | List constraint sets |
| `GET` | `.../constraint-sets/{cid}` | Get constraint set |
| `POST` | `.../constraint-sets/{cid}/validate` | Validate constraints |
| `GET` | `.../constraint-sets/{cid}/validation` | Get validation results |
| `PATCH` | `.../constraint-sets/{cid}` | Update constraint set |

### Materials

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects/{pid}/materials` | Add material |
| `GET` | `/projects/{pid}/materials` | List materials |
| `GET` | `/projects/{pid}/materials/{mid}` | Get material |
| `DELETE` | `/projects/{pid}/materials/{mid}` | Delete material |
| `GET` | `/projects/{pid}/materials/summary` | Materials summary |
| `GET` | `/material-catalog` | Full material catalog |
| `GET` | `/material-catalog/{type}` | Material type details |

### Design Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `.../sites/{sid}/design-candidates/generate` | Generate candidates |
| `GET` | `.../sites/{sid}/design-candidates` | List candidates |
| `GET` | `.../design-candidates/{cid}` | Get candidate |
| `PATCH` | `.../design-candidates/{cid}/status` | Select/reject |
| `POST` | `.../sites/{sid}/generated-designs/generate` | Generate full design |
| `POST` | `.../design-versions/from-candidate/{cid}` | Create version from candidate |
| `GET` | `.../sites/{sid}/design-versions` | List versions |
| `GET` | `.../design-versions/{vid}` | Get version |

### Validation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `.../design-versions/{vid}/validate` | Run validation |
| `GET` | `.../design-versions/{vid}/validation` | Get validation runs |
| `POST` | `.../generated-designs/{did}/validate` | Validate generated design |
| `POST` | `.../generated-designs/{did}/validate-rules` | Run YAML rule engine |
| `GET` | `/design-validation/rules` | List all YAML rules |
| `POST` | `/design-validation/reload-rules` | Hot-reload rules from disk |

### Reviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `.../design-versions/{vid}/submit-review` | Submit for review |
| `POST` | `.../reviews/{rid}/decision` | Record decision |
| `GET` | `.../design-versions/{vid}/reviews` | List reviews |

### Standards & Load Combinations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/standards/rules` | List all standards rules |
| `GET` | `/standards/rules/{id}` | Get specific rule |
| `GET` | `/standards/categories` | Rule categories |
| `GET` | `/load-combinations` | 9 ASCE 7 load combinations |
| `GET` | `/load-combinations/categories` | Combination categories |
| `GET` | `/load-combinations/governing` | Governing combination for shelters |

### BOM & Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `.../generated-designs/{did}/bom` | Bill of Materials |
| `GET` | `.../generated-designs/{did}/bom/csv` | BOM as CSV |
| `GET` | `.../generated-designs/{did}/export` | Full design export |
| `GET` | `.../generated-designs/{did}/geometry` | 3D geometry (Three.js scene) |
| `GET` | `.../generated-designs/{did}/geometry/simple` | Single truss geometry |

### Design Comparison

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/compare-designs` | Weighted comparison matrix |

### Dashboard & Activity

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/stats` | Dashboard statistics |
| `GET` | `/projects/{pid}/history` | Project timeline |
| `GET` | `/projects/{pid}/audit` | Audit event log |
| `GET` | `/projects/{pid}/activity` | Activity feed |
| `GET` | `/projects/{pid}/activity/summary` | Activity counts |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/notifications` | Notification center |

---

## Engineering Modules

### Wind Load Calculator (ASCE 7-22 §28.3)

```python
POST /api/v1/engineering/wind-load
{
  "wind_speed_mps": 38.0,        # Basic wind speed
  "exposure_category": "C",       # Open terrain
  "building_type": "enclosed",    # Enclosed structure
  "roof_angle_deg": 20.0,         # Roof pitch
  "height_m": 3.0,                # Eave height
  "length_m": 6.0,                # Along-wind dimension
  "width_m": 4.0                  # Cross-wind dimension
}
```

Returns 6-zone pressure table (zones A-F), velocity pressure qh, gust factor, and safety assessment.

### Seismic Load Calculator (ASCE 7-22 §12.8)

```python
POST /api/v1/engineering/seismic-load
{
  "seismic_zone": "3",            # Zone 1-5
  "soil_class": "D",              # Soil A-F
  "importance_factor": 1.25,      # Essential facility
  "structural_system": "wood_light_frame",
  "total_mass_kg": 5000.0,
  "height_m": 3.0,
  "num_stories": 1
}
```

Returns base shear, per-story forces, overturning moments, and drift check.

### Pareto Optimization

```python
POST /api/v1/engineering/optimize
{
  "designs": [...],               # Array of design objects
  "criteria": {
    "structural_integrity": 0.3,
    "cost_efficiency": 0.25,
    "material_availability": 0.2,
    "build_complexity": 0.15,
    "compliance": 0.1
  }
}
```

Returns Pareto-optimal designs with weighted scores and recommendations.

### PDF Report Generator

```python
POST /api/v1/engineering/generate-report
{
  "project_name": "Emergency Shelter - Camp Alpha",
  "design_version": {...},
  "wind_load": {...},
  "seismic_load": {...},
  "cost_estimate": {...},
  "validation_results": {...}
}
```

Returns a 7-section professional PDF with calculations, tables, badges, and recommendations.

---

## Validation Engine

### YAML Rule Registry (8 Rules)

| Rule ID | Category | Check | Sphere Reference |
|---------|----------|-------|-----------------|
| `R-GEO-001` | Geometry | Design span ≤ site length | §4.1 |
| `R-GEO-002` | Geometry | Member length ≤ 6m stock | §4.1 |
| `R-GEO-003` | Geometry | Interior clearance ≥ 2.0m | §4.1 |
| `R-MAT-001` | Material | At least 1 material defined | §3.2 |
| `R-MAT-002` | Material | Material exists in catalog | §3.2 |
| `R-LOAD-001` | Load Path | Connections define load path | §4.3 |
| `R-ENV-001` | Environment | Hazard scenario defined | §2.1 |
| `R-CONN-001` | Connections | Connections are defined | §4.2 |

### Engine Methods (10 evaluators)

`min_threshold`, `max_threshold`, `min_length`, `enum_exists`, `set_membership`, `positive_value`, `not_empty`, `field_lte_field`, `field_gte_field`, `connectivity_check`

### Usage

```python
from app.validator import validate_design, build_context, list_rules

# List all rules
rules = list_rules()  # Returns 8 rules

# Build validation context from design data
context = build_context(
    design_version=version,
    constraint_set=constraints,
    materials=materials
)

# Run all rules
report = validate_design(context)
# report.verdict: "pass" | "fail" | "not_evaluated"
# report.results: List[RuleResult]
# report.passed: int, report.failed: int, report.skipped: int
```

---

## Platform Services

### Background Job Queue

```python
# Create a job
POST /api/v1/platform/jobs
{"type": "design_generation", "payload": {...}, "priority": "high"}

# Check status
GET /api/v1/platform/jobs/{job_id}

# Cancel / retry
POST /api/v1/platform/jobs/{job_id}/cancel
POST /api/v1/platform/jobs/{job_id}/retry
```

### API Key Management

```python
# Generate key
POST /api/v1/platform/api-keys
{"name": "My App", "tier": "pro"}

# Rate limits by tier:
#   free:       60 requests/minute
#   pro:       600 requests/minute
#   enterprise: 6000 requests/minute
```

### Webhooks

```python
# Register
POST /api/v1/platform/webhooks
{"url": "https://example.com/hook", "events": ["design.validated", "review.completed"]}

# Available events:
#   design.generated, design.validated, design.approved,
#   review.completed, validation.completed, job.completed
```

### Geo-Climate Lookup

```python
POST /api/v1/platform/geo-climate
{"latitude": 33.6941, "longitude": 73.0479}

# Returns: climate zone, hazards, recommended materials
```

### 3D Model Export

```python
POST /api/v1/platform/export/gltf   # glTF 2.0 (WebGL)
POST /api/v1/platform/export/ifc    # IFC (BIM software)
POST /api/v1/platform/export/obj    # OBJ (3D printers)
```

---

## 3D Viewer

Open `docs/viewer3d.html` in any modern browser for an interactive Three.js workspace.

### Features

| Feature | Controls |
|---------|----------|
| **Orbit** | Left mouse drag |
| **Pan** | Middle mouse drag |
| **Zoom** | Scroll wheel |
| **Select member** | Left click → highlights green, shows cross-section |
| **Hover tooltip** | Shows type, length, diameter, material |
| **View presets** | Front / Side / Top / 3D Perspective buttons |
| **Wireframe mode** | Toggle button in toolbar |
| **Dimensions** | Toggle measurement lines |
| **Node joints** | Toggle connection point spheres |
| **Member list** | Scrollable sidebar with all members |

### Color Scheme (matches UI screenshots)

| Element | Color |
|---------|-------|
| Nav bar | `#0C252A` (dark teal) |
| 3D background | `#131D1F` (dark) |
| Right panel | `#FFFFFF` (white) |
| Sage accent | `#D5DDD2` |
| Light blue tint | `#EAF5F9` |
| Member green | `#40916C` |
| Rafter gold | `#D4A373` |

---

## Testing

**417 tests** across 13 test files, all passing.

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --tb=short -q

# Run specific test modules
python -m pytest tests/test_engineering.py -v      # 40 tests
python -m pytest tests/test_platform.py -v          # 36 tests
python -m pytest tests/test_validator_engine.py -v  # 24 tests
python -m pytest tests/test_e2e_pipeline.py -v      # End-to-end
```

### Test Breakdown

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_e2e_pipeline.py` | ~50 | Full pipeline: project → site → constraints → generation → validation → review |
| `test_engineering.py` | 40 | Wind, seismic, optimization, cost, safety, substitution, templates, diff, report |
| `test_platform.py` | 36 | Job queue, API keys, rate limiting, webhooks, cache, geo-climate, export |
| `test_validator_engine.py` | 24 | All 8 YAML rules: pass/fail/edge cases |
| `test_structural_analysis.py` | ~15 | Load paths, member analysis |
| `test_analysis_service.py` | ~12 | Analysis service + schemas |
| `test_compliance_service.py` | ~14 | Compliance reporting |
| `test_constraint_set_pipeline.py` | ~20 | Constraint building + validation |
| Others | ~200+ | Individual module tests |

---

## Deployment

### Local Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker-ready)

```bash
# The app is designed for containerized deployment
# Database: Switch from SQLite to PostgreSQL
# Storage: Switch from local to Alibaba Cloud OSS
# AI: Switch from mock to Qwen provider
# Queue: Add Redis + worker for async generation
```

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./panah.db          # Development
DATABASE_URL=postgresql://user:pass@host/db # Production

# AI Provider
AI_PROVIDER=mock                           # MVP
AI_PROVIDER=qwen                           # Production (Alibaba Cloud)

# Storage
STORAGE_BACKEND=local                      # MVP
STORAGE_BACKEND=oss                        # Production (Alibaba Cloud OSS)
```

---

## UI Screenshots

| Screen | Description |
|--------|-------------|
| ![Dashboard](docs/screenshots/01_dashboard.jpeg) | **Dashboard** — Project overview, quick actions, statistics |
| ![Requirements](docs/screenshots/02_requirements.jpeg) | **Requirements** — Family size, site dimensions, climate, structural properties |
| ![Materials](docs/screenshots/03_materials.jpeg) | **Materials** — Local material inventory with properties |
| ![Generation](docs/screenshots/04_generation.jpeg) | **Generation** — Candidate design generation and selection |
| ![3D Workspace](docs/screenshots/05_3d_workspace.jpeg) | **Material Library** — Material cards with specs and pricing |
| ![Validation](docs/screenshots/06_validation.jpeg) | **Validation** — Deterministic rule checking with pass/fail results |
| ![Review](docs/screenshots/07_review.jpeg) | **Engineer Review** — Decision recording and audit trail |

---

## What This Is Not

- ❌ A fully autonomous structural engineer
- ❌ A replacement for professional engineering approval
- ❌ A complete building-code certification engine
- ❌ A full finite-element analysis platform

> **Panagah is a decision-support tool.** Every design requires human engineer review before construction.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python -m pytest tests/ -v`)
4. Commit your changes
5. Push to the branch and open a Pull Request

---

## License

Built for humanitarian shelter assessment. Use responsibly.

---

<div align="center">

**Built with ❤️ for humanitarian shelter assessment**

[![GitHub](https://img.shields.io/badge/GitHub-HaiqaKaleem%2FPanah-181717?style=flat-square&logo=github)](https://github.com/HaiqaKaleem/Panah)

</div>
