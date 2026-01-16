---
phase: 02-extraction-pipeline
plan: 02
subsystem: extraction
tags: [instructor, claude, anthropic, ai, extraction, confidence]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: [config, settings]
provides:
  - Instructor + Claude client wrapper
  - BaseExtractor abstract class
  - FieldConfidence pattern for field-level confidence
  - ExtractionMetadata for audit trail
affects: [02-03, 02-04, 02-05, extraction-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [instructor-anthropic-json, field-confidence, base-extractor]

key-files:
  created:
    - app/core/extraction/schemas.py
    - app/core/extraction/client.py
    - app/core/extraction/base.py
    - app/core/extraction/__init__.py
  modified:
    - app/config.py

key-decisions:
  - "ANTHROPIC_JSON mode for structured output (reliable JSON parsing)"
  - "Tenacity retry with exponential backoff (1-30s)"
  - "0.7 confidence threshold for needs_review flag"
  - "Recursive field scanning to check all FieldConfidence instances"
  - "claude-sonnet-4-20250514 as default model"

patterns-established:
  - "FieldConfidence: value + confidence + source_text for every extracted field"
  - "BaseExtractor: abstract class all test extractors inherit"
  - "extract_structured: generic function for any Pydantic model"

# Metrics
duration: ~12min
completed: 2026-01-15
---

# Phase 02-02: Instructor + Claude Integration Summary

**Instructor client with Claude for structured extraction, retry logic, and confidence patterns**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-01-15
- **Tasks:** 3
- **Files created:** 4
- **Files modified:** 1

## Accomplishments

- Created extraction schemas with field-level confidence tracking
- Built Instructor-wrapped Claude client with retry and Vision support
- Implemented BaseExtractor abstract class for all test extractors
- Added ANTHROPIC_API_KEY configuration setting

## Task Commits

1. **Task 1: Create extraction schemas** - `21c99e5` (feat)
2. **Task 2: Create Instructor client** - `f34a757` (feat)
3. **Task 3: Create base extractor** - `cec2404` (feat)

## Files Created

| Path | Purpose | Lines |
|------|---------|-------|
| `app/core/extraction/schemas.py` | FieldConfidence, ExtractionMetadata, BaseExtractionResult | 115 |
| `app/core/extraction/client.py` | Instructor client, extract_structured | 165 |
| `app/core/extraction/base.py` | BaseExtractor abstract class | 155 |
| `app/core/extraction/__init__.py` | Module exports | 40 |

## Key Architecture Decisions

1. **ANTHROPIC_JSON mode**: More reliable than tool_use for structured extraction
2. **Tenacity retry**: Exponential backoff 1-30s for API resilience
3. **0.7 threshold**: Balance between flagging issues and avoiding false positives
4. **Recursive field check**: Automatically scan nested models for low confidence

## Requirements Addressed

- [x] EXTR-09: System retries extraction on validation failure (max 3 attempts)
- [x] Foundation for EXTR-07 (confidence scoring pattern established)

## Key Links

| From | To | Via |
|------|-----|-----|
| `base.py` | `client.py` | extract_structured |
| `base.py` | `schemas.py` | BaseExtractionResult, FieldConfidence |
| `client.py` | `schemas.py` | ExtractionMetadata |
| `client.py` | `app/config.py` | ANTHROPIC_API_KEY |

## Extraction Patterns

```python
# Field with confidence
equipment_tag: FieldConfidence  # value, confidence, source_text

# Base result with metadata
class GroundingResult(BaseExtractionResult):
    equipment: EquipmentInfo
    measurements: list[GroundingMeasurement]

# Using base extractor
class GroundingExtractor(BaseExtractor):
    @property
    def test_type(self) -> str:
        return "grounding"

    @property
    def system_prompt(self) -> str:
        return "Extract grounding test data..."

    def get_response_model(self) -> type[BaseExtractionResult]:
        return GroundingResult
```

## Next Steps

- Plan 02-03: Grounding test extraction schema (first concrete extractor)
- Plan 02-04: Megger test extraction schema
- Plan 02-05: Thermography extraction with Vision

---
*Phase: 02-extraction-pipeline*
*Plan: 02*
*Completed: 2026-01-15*
