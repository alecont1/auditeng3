# Phase 4: Standards Configuration - Context

**Gathered:** 2026-01-16
**Status:** Ready for planning

<vision>
## How This Should Work

**Original roadmap said RAG — but that's overengineering.**

The technical standards (NETA, IEEE, Microsoft CxPOR) have finite, well-defined limits. The validation is DETERMINISTIC: AI extracts the value, CODE compares with fixed limits. Results are predictable and auditable.

Semantic search makes no sense here — the thresholds don't need "retrieval." They need proper structuring.

**What Phase 4 actually does:**
Transform the existing `config.py` thresholds into a complete standards configuration system where:
- Every limit is linked to its source standard
- Projects can choose which standard applies (NETA general vs Microsoft Data Center)
- Audit trails reference the exact standard clause

</vision>

<essential>
## What Must Be Nailed

- **Single source of truth** — All limits in one config module that validators reference — no hardcoded values scattered in code. (Already partially done in Phase 3's `config.py`)

- **Multi-standard support** — Same test can be validated against different standards (NETA vs Microsoft) based on project requirements. Currently missing.

- **Audit traceability** — Every threshold links back to its source standard (e.g., "IEEE 43-2013 Section 12.3"). Currently missing.

</essential>

<specifics>
## Specific Ideas

- Standards already documented in the user's knowledge:
  - NETA ATS → Grounding ≤10Ω general, Megger by voltage class
  - Microsoft CxPOR → Grounding ≤5Ω (more restrictive for data centers)
  - IEEE 43 → Insulation resistance and Polarization Index

- The config should support switching between "NETA" and "MICROSOFT" profiles
- Each threshold needs a `standard_reference` field linking to the source

</specifics>

<notes>
## Additional Context

Phase 3 already has a solid foundation in `app/core/validation/config.py`:
- `ValidationConfig` aggregates all thresholds
- `lru_cache` ensures determinism
- Equipment-type-specific thresholds exist

What's missing:
1. Multi-standard profiles (NETA vs Microsoft)
2. Standard reference traceability per threshold
3. Ability to select standard profile per project/analysis

This phase builds ON TOP of Phase 3's work, not replacing it.

**Name change:** Phase 4 should be renamed from "RAG Pipeline" to "Standards Configuration" to reflect the actual work.

</notes>

---

*Phase: 04-standards-config*
*Context gathered: 2026-01-16*
