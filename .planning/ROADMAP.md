# Roadmap: AuditEng

## Overview

Build an automated electrical commissioning report validation system following the "AI extrai, código valida" principle. The journey progresses from foundation infrastructure through AI extraction, deterministic validation, RAG-enhanced intelligence, complete API, and finally reporting with full audit trails.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Foundation** - Data models, database setup, and background job infrastructure
- [ ] **Phase 2: Extraction Pipeline** - Document upload and AI extraction with Claude + Instructor
- [ ] **Phase 3: Validation Engine** - Deterministic validation rules against NETA/IEEE standards
- [ ] **Phase 4: RAG Pipeline** - Technical standards indexing and retrieval with pgvector
- [ ] **Phase 5: API & Findings** - REST API endpoints and finding/verdict generation
- [ ] **Phase 6: Reporting & Audit** - PDF report generation and comprehensive audit trails

## Phase Details

### Phase 1: Foundation
**Goal**: Establish core infrastructure with database models, migrations, and reliable background job processing
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, PROC-01, PROC-02, PROC-03, PROC-04, PROC-05
**Success Criteria** (what must be TRUE):
  1. Database schema is created with all core models (User, Task, Analysis, Finding)
  2. Alembic migrations run successfully and are version-controlled
  3. Dramatiq workers can enqueue and process jobs with retry logic
  4. Development environment runs with PostgreSQL + Redis
  5. Basic health check endpoint returns 200 OK
**Research**: Unlikely (established patterns from research)
**Plans**: 5 plans (complete)

Plans:
- [x] 01-01: Project structure and Pydantic schemas
- [x] 01-02: SQLAlchemy models and async config
- [x] 01-03: Alembic migrations
- [x] 01-04: Dramatiq job queue with Redis
- [x] 01-05: FastAPI application and health checks

### Phase 2: Extraction Pipeline
**Goal**: Users can upload commissioning report PDFs and receive structured extracted data with confidence scores
**Depends on**: Phase 1
**Requirements**: UPLD-01, UPLD-02, UPLD-03, UPLD-04, UPLD-05, UPLD-06, EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05, EXTR-06, EXTR-07, EXTR-08, EXTR-09, EXTR-10
**Success Criteria** (what must be TRUE):
  1. User can upload PDF files up to 50MB via API
  2. System extracts structured data from Grounding test reports
  3. System extracts structured data from Megger test reports
  4. System extracts structured data from Thermography reports (including thermal images)
  5. Each extracted field has a confidence score between 0 and 1
  6. Low-confidence extractions are flagged for review
  7. Failed extractions retry up to 3 times automatically
**Research**: Likely (Claude Vision integration, Instructor patterns)
**Research topics**: Claude PDF/Vision API current patterns, Instructor retry configuration, PyMuPDF extraction quality
**Plans**: TBD

Plans:
- [x] 02-01: File upload and storage
- [x] 02-02: Instructor + Claude integration
- [x] 02-03: Grounding test extraction schema
- [x] 02-04: Megger test extraction schema
- [x] 02-05: Thermography extraction with Vision
- [ ] 02-06: Confidence scoring and retry logic

### Phase 3: Validation Engine
**Goal**: Extracted data is validated deterministically against NETA/IEEE standards with consistent, reproducible results
**Depends on**: Phase 2
**Requirements**: VALD-01, VALD-02, VALD-03, VALD-04, VALD-05, VALD-06, VALD-07, VALD-08, VALD-09
**Success Criteria** (what must be TRUE):
  1. Grounding resistance values are validated against NETA/IEEE thresholds
  2. Insulation resistance values are validated against IEEE 43 standards
  3. Thermography temperature deltas are classified by severity thresholds
  4. Calibration certificate expiration dates are validated
  5. Same input data always produces identical validation results (deterministic)
  6. Validation thresholds are externalized in configuration files
  7. Equipment-type-specific rules (PANEL, UPS, ATS, GEN, XFMR) are applied correctly
**Research**: Likely (NETA/IEEE threshold values, rule engine patterns)
**Research topics**: NETA ATS-2025 thresholds, IEEE 43 insulation testing, equipment-specific compliance requirements
**Plans**: TBD

Plans:
- [ ] 03-01: Validation rule framework
- [ ] 03-02: Grounding validation rules
- [ ] 03-03: Megger validation rules (IEEE 43)
- [ ] 03-04: Thermography validation rules
- [ ] 03-05: Calibration and cross-field validation
- [ ] 03-06: Equipment-type-specific thresholds

### Phase 4: RAG Pipeline
**Goal**: Technical standards (NETA, IEEE, Microsoft CxPOR) are indexed and retrievable to provide context during validation
**Depends on**: Phase 1
**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, RAG-06
**Success Criteria** (what must be TRUE):
  1. Technical standards documents are chunked using semantic boundaries (256-512 tokens)
  2. Chunks are embedded using text-embedding-3-small
  3. Embeddings are stored in pgvector with HNSW indexing
  4. Hybrid search (vector + keyword) retrieves relevant standard sections
  5. Retrieved standards can be injected as context during validation
**Research**: Likely (pgvector setup, embedding model choice, chunking strategy)
**Research topics**: pgvector HNSW configuration, semantic chunking for technical documents, hybrid search patterns
**Plans**: TBD

Plans:
- [ ] 04-01: pgvector extension setup
- [ ] 04-02: Document ingestion and chunking
- [ ] 04-03: Embedding generation pipeline
- [ ] 04-04: Hybrid search implementation
- [ ] 04-05: Context retrieval for validation

### Phase 5: API & Findings
**Goal**: Complete REST API with authentication, and finding generation with severity classification and verdicts
**Depends on**: Phase 2, Phase 3
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, API-07, FIND-01, FIND-02, FIND-03, FIND-04, FIND-05, FIND-06, FIND-07, FIND-08, FIND-09
**Success Criteria** (what must be TRUE):
  1. API accepts document submission with JWT authentication
  2. API returns analysis status via polling endpoint
  3. API returns complete analysis results with findings
  4. Rate limiting prevents abuse (10 requests/minute per user)
  5. Findings have severity levels (CRITICAL, MAJOR, MINOR, INFO)
  6. Compliance score (0-100%) is computed from findings
  7. Verdicts (APPROVED, REVIEW, REJECTED) are determined correctly
  8. Each finding includes evidence and remediation guidance
  9. OpenAPI/Swagger documentation is generated automatically
**Research**: Unlikely (established FastAPI patterns)
**Plans**: TBD

Plans:
- [ ] 05-01: Authentication endpoints (JWT)
- [ ] 05-02: Document submission API
- [ ] 05-03: Status and results endpoints
- [ ] 05-04: Finding generation service
- [ ] 05-05: Scoring and verdict logic
- [ ] 05-06: Rate limiting and OpenAPI docs

### Phase 6: Reporting & Audit
**Goal**: Generate professional PDF reports with findings summaries and maintain complete audit trails for compliance
**Depends on**: Phase 5
**Requirements**: REPT-01, REPT-02, REPT-03, REPT-04, REPT-05, REPT-06, AUDT-01, AUDT-02, AUDT-03, AUDT-04, AUDT-05, AUDT-06
**Success Criteria** (what must be TRUE):
  1. PDF report includes findings summary with severity indicators
  2. PDF report includes equipment identification and test metadata
  3. PDF report includes compliance score and verdict
  4. PDF report includes standard references for each finding
  5. User can download PDF report via API
  6. All extraction attempts are logged with timestamps
  7. All validation decisions are logged with rule IDs
  8. Model and prompt versions are tracked in audit logs
  9. Audit logs are immutable (append-only)
  10. User can retrieve complete audit trail for any analysis
**Research**: Unlikely (ReportLab/WeasyPrint patterns)
**Plans**: TBD

Plans:
- [ ] 06-01: PDF report template design
- [ ] 06-02: Report generation service
- [ ] 06-03: Audit logging infrastructure
- [ ] 06-04: Audit trail API endpoints

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 5/5 | Complete | 2026-01-15 |
| 2. Extraction Pipeline | 5/6 | In progress | - |
| 3. Validation Engine | 0/6 | Not started | - |
| 4. RAG Pipeline | 0/5 | Not started | - |
| 5. API & Findings | 0/6 | Not started | - |
| 6. Reporting & Audit | 0/4 | Not started | - |

**Total:** 10/32 plans complete (31%)

---
*Roadmap created: 2026-01-15*
*Requirements coverage: 61/61 (100%)*
