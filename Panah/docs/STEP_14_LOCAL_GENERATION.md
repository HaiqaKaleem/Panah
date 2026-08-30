# Step 14 — Local Constraint-Driven Generation

## Decision

Panah must be able to run its complete hackathon MVP without Alibaba Cloud,
Qwen access, network model APIs, or provider credentials.

Therefore the MVP generation layer is implemented locally.

## Flow

ConstraintSet
→ LocalGenerationService
→ 1–3 structured candidate designs
→ DesignVersion conversion
→ geometry
→ deterministic validation
→ review

## What this generator is

It is a deterministic constraint-driven candidate generator for the MVP.
It produces parametric roof-truss candidates rather than arbitrary mesh data.

The generator:
- reads the canonical ConstraintSet
- preserves material IDs
- creates structured members and connections
- produces multiple candidate variants
- requires no network access

## What it is not

It is not a structural safety authority and it does not calculate PASS/FAIL.
Validation remains a separate backend responsibility.

It is also not pretending to be an LLM. The generation method is explicitly
recorded as `local_constraint_generator`.

## Why this is safer for the hackathon

The demo no longer depends on:
- Alibaba access
- Qwen availability
- API keys
- network reliability
- sponsor tooling availability

A future AI provider can be added later without changing the downstream
DesignVersion → geometry → validation → review pipeline.

## Candidate strategy

Three deterministic candidates are available:

1. Direct/site-sized candidate — useful for demonstrating a validator failure.
2. Conservative material-length candidate.
3. Compact alternative candidate.

The validator, not the generator, decides whether a candidate passes.

## Next backend step

Convert `GenerationCandidate` into the existing canonical `DesignVersion`.
That conversion is where application-owned schema rules remain authoritative.
