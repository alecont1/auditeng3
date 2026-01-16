---
phase: 02-extraction-pipeline
plan: 05
subsystem: extraction
tags: [thermography, vision, claude-vision, hotspot, neta-mts, thermal-imaging]

# Dependency graph
requires:
  - phase: 02-02
    provides: [BaseExtractor, FieldConfidence, extract_structured]
provides:
  - ThermographyExtractor for thermal image analysis
  - ThermographyExtractionResult with hotspot detection
  - THERMOGRAPHY_EXTRACTION_PROMPT for Vision
affects: [02-06, validation-engine]

# Tech tracking
tech-stack:
  added: []
  patterns: [vision-api, delta-t-calculation, neta-severity]

key-files:
  created:
    - app/core/extraction/thermography.py
    - app/core/extraction/prompts/thermography.py
  modified:
    - app/core/extraction/__init__.py
    - app/core/extraction/prompts/__init__.py

key-decisions:
  - "NETA MTS severity thresholds: 5/15/35/70°C"
  - "Emissivity expected 0.95 for electrical equipment"
  - "Critical/serious hotspots always flag for review"
  - "extract_from_images handles base64 encoding"

patterns-established:
  - "Vision extraction via base64-encoded images"
  - "Severity classification with StrEnum"
  - "Hotspot-level calculations in model_post_init"

# Metrics
duration: ~10min
completed: 2026-01-15
---

# Phase 02-05: Thermography Extraction Summary

**ThermographyExtractor with Claude Vision for hotspot detection and NETA severity**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-01-15
- **Tasks:** 3
- **Files created:** 2
- **Files modified:** 2

## Accomplishments

- Created HotspotSeverity enum with NETA MTS classifications
- Created Hotspot schema with automatic delta-T and severity calculation
- Created ThermographyExtractionResult with summary statistics
- Built Vision-ready extraction prompt with image analysis guidance
- Implemented ThermographyExtractor with emissivity validation

## Task Commits

1. **All tasks combined** - `238303b` (feat)

## Files Created

| Path | Purpose | Lines |
|------|---------|-------|
| `app/core/extraction/thermography.py` | Thermography schemas and extractor | 250 |
| `app/core/extraction/prompts/thermography.py` | Vision extraction prompt | 65 |

## NETA MTS Severity Classification

| Severity | Delta-T Range | Action Required |
|----------|---------------|-----------------|
| NORMAL | < 5°C | No action |
| ATTENTION | 5-15°C | Schedule at next opportunity |
| INTERMEDIATE | 15-35°C | Repair within 1 month |
| SERIOUS | 35-70°C | Immediate repair, reduce load |
| CRITICAL | > 70°C | Immediate de-energization |

## Schema Structure

```python
ThermographyExtractionResult:
├── equipment: EquipmentInfo
├── calibration: CalibrationInfo | None
├── test_conditions: ThermographyTestConditions
│   ├── inspection_date: FieldConfidence
│   ├── load_conditions: FieldConfidence | None
│   └── camera_model: FieldConfidence | None
├── thermal_data: ThermalImageData
│   ├── emissivity: FieldConfidence | None
│   ├── ambient_temperature: FieldConfidence | None
│   └── reflected_temperature: FieldConfidence | None
├── hotspots: list[Hotspot]
│   ├── location: FieldConfidence
│   ├── max_temperature: FieldConfidence
│   ├── reference_temperature: FieldConfidence
│   └── derived: delta_t, severity
└── derived: max_delta_t, max_severity, critical_count, serious_count
```

## Requirements Addressed

- [x] EXTR-03: System extracts structured data from Thermography reports
- [x] EXTR-10: System processes thermal images using Claude Vision

## Key Links

| From | To | Via |
|------|-----|-----|
| `thermography.py` | `base.py` | extends BaseExtractor |
| `thermography.py` | `client.py` | uses extract_structured with images |
| `thermography.py` | `prompts/thermography.py` | imports THERMOGRAPHY_EXTRACTION_PROMPT |
| `__init__.py` | `thermography.py` | exports ThermographyExtractor |

## Next Steps

- Plan 02-06: Confidence scoring and retry logic refinement
- Phase 3: Validation engine using NETA severity thresholds

---
*Phase: 02-extraction-pipeline*
*Plan: 05*
*Completed: 2026-01-15*
