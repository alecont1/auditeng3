---
phase: 02-extraction-pipeline
plan: 06
subsystem: extraction
tags: [orchestration, pipeline, worker, dramatiq, status-api]

# Dependency graph
requires:
  - phase: 02-01
    provides: [save_file, storage service]
  - phase: 02-02
    provides: [BaseExtractor, extract_structured]
  - phase: 02-03
    provides: [GroundingExtractor]
  - phase: 02-04
    provides: [MeggerExtractor]
  - phase: 02-05
    provides: [ThermographyExtractor]
provides:
  - process_document for end-to-end extraction
  - detect_test_type for automatic classification
  - process_document_task Dramatiq actor
  - Task status and result API endpoints
affects: [phase-3-validation, phase-5-api]

# Tech tracking
tech-stack:
  added: [pymupdf]
  patterns: [orchestration, dramatiq-actor, async-worker]

key-files:
  created:
    - app/services/extraction.py
    - app/worker/extraction.py
    - app/api/tasks.py
  modified:
    - app/services/__init__.py
    - app/worker/__init__.py
    - app/api/upload.py
    - app/main.py

key-decisions:
  - "Keyword-based test type detection (not AI)"
  - "PyMuPDF for PDF text and image extraction"
  - "Dramatiq actor with max_retries=3"
  - "202 Accepted for in-progress results"

patterns-established:
  - "Orchestration service coordinates extractors"
  - "Worker stores Analysis record with extraction_result"
  - "Redis job status tracks needs_review flag"

# Metrics
duration: ~15min
completed: 2026-01-15
---

# Phase 02-06: Extraction Pipeline Orchestration Summary

**Complete extraction pipeline from upload to stored results with status tracking**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-01-15
- **Tasks:** 3
- **Files created:** 3
- **Files modified:** 4

## Accomplishments

- Created extraction orchestration service with test type detection
- Built PDF text and image extraction using PyMuPDF
- Implemented Dramatiq actor for background processing
- Created task status endpoint (GET /api/tasks/{task_id})
- Created task result endpoint (GET /api/tasks/{task_id}/result)
- Integrated all three extractors (Grounding, Megger, Thermography)
- Updated upload endpoint to use real extraction worker

## Task Commits

1. **All tasks combined** - `f285f2b` (feat)

## Files Created

| Path | Purpose | Lines |
|------|---------|-------|
| `app/services/extraction.py` | Extraction orchestration | 215 |
| `app/worker/extraction.py` | Dramatiq background task | 150 |
| `app/api/tasks.py` | Task status/result endpoints | 175 |

## Pipeline Flow

```
Upload (POST /api/upload)
    ↓
Task created (status: QUEUED)
    ↓
Dramatiq enqueues process_document_task
    ↓
Worker: process_document_task
    ↓
1. Get Task from DB
2. Update status → PROCESSING
3. Detect file type (PDF/image)
4. Extract content (text/images)
5. Auto-detect test type
6. Route to appropriate extractor
7. Create Analysis record
8. Update status → COMPLETED
    ↓
Query (GET /api/tasks/{id}/result)
```

## Test Type Detection

Uses keyword matching for classification:

| Test Type | Keywords |
|-----------|----------|
| grounding | ground resistance, earth resistance, aterramento |
| megger | insulation resistance, IR test, polarization index |
| thermography | thermal, infrared, temperature, hotspot |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/tasks/{task_id} | Get task status |
| GET | /api/tasks/{task_id}/result | Get full analysis result |

## Response Codes

- **200 OK**: Task found, result available
- **202 Accepted**: Task still processing (for /result)
- **404 Not Found**: Task doesn't exist

## Requirements Addressed

- [x] UPLD-04: User can view processing status of uploaded documents
- [x] UPLD-06: System handles multi-page PDF documents
- [x] EXTR-07: System assigns confidence score to each extracted field
- [x] EXTR-08: System flags low-confidence extractions for review
- [x] EXTR-09: System retries extraction on failure (max 3 attempts)

## Key Links

| From | To | Via |
|------|-----|-----|
| `upload.py` | `extraction.py` | enqueues process_document_task |
| `extraction.py` (worker) | `extraction.py` (service) | calls process_document |
| `extraction.py` (service) | extractors | routes by test type |
| `tasks.py` | Task, Analysis | queries status and result |

## Next Steps

- Phase 3: Validation Engine using extracted data
- Phase 5: Authentication and enhanced API

---
*Phase: 02-extraction-pipeline*
*Plan: 06*
*Completed: 2026-01-15*
