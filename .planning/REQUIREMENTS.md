# Requirements: AuditEng

**Defined:** 2026-01-15
**Core Value:** "IA extrai, código valida" — AI extraction + deterministic validation ensures reproducibility, explainability, and traceability of every finding.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Document Upload & Processing (UPLD)

- [ ] **UPLD-01**: User can upload PDF files up to 50MB
- [ ] **UPLD-02**: User can upload image files (PNG, JPG, TIFF) for thermal images
- [ ] **UPLD-03**: System queues uploaded documents for background processing
- [ ] **UPLD-04**: User can view processing status of uploaded documents
- [ ] **UPLD-05**: System stores original documents for reprocessing capability
- [ ] **UPLD-06**: System handles multi-page PDF documents with page-level processing

### AI Extraction (EXTR)

- [ ] **EXTR-01**: System extracts structured data from Grounding test reports
- [ ] **EXTR-02**: System extracts structured data from Megger (insulation resistance) test reports
- [ ] **EXTR-03**: System extracts structured data from Thermography inspection reports
- [ ] **EXTR-04**: System extracts equipment identification (TAG, serial number, type)
- [ ] **EXTR-05**: System extracts test measurements with units
- [ ] **EXTR-06**: System extracts calibration certificate information (expiration, traceability)
- [ ] **EXTR-07**: System assigns confidence score (0-1) to each extracted field
- [ ] **EXTR-08**: System flags low-confidence extractions for human review
- [ ] **EXTR-09**: System retries extraction on validation failure (max 3 attempts)
- [ ] **EXTR-10**: System processes thermal images using Claude Vision

### Validation Engine (VALD)

- [ ] **VALD-01**: System validates grounding resistance against NETA/IEEE thresholds
- [ ] **VALD-02**: System validates insulation resistance against IEEE 43 standards
- [ ] **VALD-03**: System validates thermography temperature deltas against severity thresholds
- [ ] **VALD-04**: System validates calibration certificate expiration dates
- [ ] **VALD-05**: System performs cross-field validation (equipment TAG consistency)
- [ ] **VALD-06**: System validates measurement units are present and consistent
- [ ] **VALD-07**: Validation produces identical results for identical inputs (deterministic)
- [ ] **VALD-08**: Validation rules are externalized in configuration (not hard-coded)
- [ ] **VALD-09**: System validates against equipment-type-specific thresholds (PANEL, UPS, ATS, GEN, XFMR)

### RAG Pipeline (RAG)

- [ ] **RAG-01**: System indexes technical standards documents (NETA, IEEE, Microsoft CxPOR)
- [ ] **RAG-02**: System chunks standards using semantic boundaries (256-512 tokens)
- [ ] **RAG-03**: System embeds chunks using text-embedding-3-small
- [ ] **RAG-04**: System stores embeddings in pgvector (PostgreSQL)
- [ ] **RAG-05**: System retrieves relevant standard sections during validation
- [ ] **RAG-06**: System supports hybrid search (vector + keyword)

### Findings & Verdicts (FIND)

- [ ] **FIND-01**: System generates findings with severity levels (CRITICAL, MAJOR, MINOR, INFO)
- [ ] **FIND-02**: System assigns severity based on validation rule violations
- [ ] **FIND-03**: System computes compliance score (0-100%)
- [ ] **FIND-04**: System computes confidence score based on extraction quality
- [ ] **FIND-05**: System determines verdict: APPROVED (no CRITICAL, score >= 95%)
- [ ] **FIND-06**: System determines verdict: REVIEW (score 80-94% or low confidence)
- [ ] **FIND-07**: System determines verdict: REJECTED (any CRITICAL finding)
- [ ] **FIND-08**: Each finding includes evidence (extracted value, threshold, standard reference)
- [ ] **FIND-09**: Findings include remediation guidance

### API & Integration (API)

- [ ] **API-01**: System provides REST API for document submission
- [ ] **API-02**: System provides REST API for analysis status polling
- [ ] **API-03**: System provides REST API for retrieving analysis results
- [ ] **API-04**: API requires authentication (JWT tokens)
- [ ] **API-05**: API includes rate limiting (10 requests/minute per user)
- [ ] **API-06**: API returns structured JSON responses with proper error codes
- [ ] **API-07**: API documentation available via OpenAPI/Swagger

### Reporting (REPT)

- [ ] **REPT-01**: System generates PDF report with findings summary
- [ ] **REPT-02**: Report includes equipment identification and test metadata
- [ ] **REPT-03**: Report includes detailed findings with severity indicators
- [ ] **REPT-04**: Report includes compliance score and verdict
- [ ] **REPT-05**: Report includes standard references for each finding
- [ ] **REPT-06**: User can download PDF report via API

### Audit Trail (AUDT)

- [ ] **AUDT-01**: System logs all extraction attempts with timestamps
- [ ] **AUDT-02**: System logs all validation decisions with rule IDs
- [ ] **AUDT-03**: System logs model version and prompt version used
- [ ] **AUDT-04**: System logs confidence scores for each extraction
- [ ] **AUDT-05**: Audit logs are immutable (append-only)
- [ ] **AUDT-06**: User can retrieve audit trail for any analysis

### Background Processing (PROC)

- [x] **PROC-01**: System uses Dramatiq for reliable job queue processing
- [x] **PROC-02**: Jobs retry on failure with exponential backoff
- [x] **PROC-03**: System supports job prioritization
- [x] **PROC-04**: System provides job status tracking
- [x] **PROC-05**: System handles graceful degradation on partial failures

### Data Models (DATA)

- [x] **DATA-01**: System stores analysis results in PostgreSQL
- [x] **DATA-02**: System uses SQLAlchemy 2.0 with async support
- [x] **DATA-03**: System uses Alembic for database migrations
- [x] **DATA-04**: System stores user and authentication data
- [x] **DATA-05**: System stores document metadata and storage references

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Human-in-the-Loop (HITL)

- **HITL-01**: User can review low-confidence extractions
- **HITL-02**: User can correct extracted values inline
- **HITL-03**: Corrections are captured for model improvement
- **HITL-04**: System routes uncertain items to appropriate reviewers
- **HITL-05**: Review queue prioritizes by confidence and business impact

### Appeal & Override (APPL)

- **APPL-01**: User can dispute automated findings
- **APPL-02**: User can attach evidence to disputes
- **APPL-03**: Override requires justification
- **APPL-04**: Override decisions are logged in audit trail
- **APPL-05**: Multi-level approval for critical overrides

### Analytics & Dashboard (DASH)

- **DASH-01**: Dashboard shows compliance trends over time
- **DASH-02**: Dashboard shows equipment risk heat maps
- **DASH-03**: Dashboard shows extraction accuracy metrics
- **DASH-04**: Dashboard supports drill-down to individual findings
- **DASH-05**: Dashboard exports analytics data

### Advanced Extraction (ADVX)

- **ADVX-01**: System handles handwritten annotations
- **ADVX-02**: System performs multi-pass extraction for complex documents
- **ADVX-03**: System detects and handles table continuation across pages
- **ADVX-04**: System extracts data from charts and diagrams

### Notifications (NOTF)

- **NOTF-01**: User receives notification when analysis completes
- **NOTF-02**: User receives alert for CRITICAL findings
- **NOTF-03**: User can configure notification preferences
- **NOTF-04**: System supports email notifications

### Multi-tenancy (MTNT)

- **MTNT-01**: System supports multiple companies/organizations
- **MTNT-02**: Data isolation between tenants
- **MTNT-03**: Tenant-specific validation thresholds
- **MTNT-04**: Tenant-specific branding on reports

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Mobile app nativo | Focus on web/API first per PROJECT.md |
| Integração com Procore/externos | MVP standalone per PROJECT.md |
| Geração automática de relatórios PDF completos | Basic PDF only for MVP, full reports deferred |
| Multi-idioma | English only for MVP per PROJECT.md |
| Frontend web completo | API-first approach, basic UI only |
| Real-time WebSocket updates | Polling sufficient for MVP |
| Video processing | Not relevant to commissioning reports |
| Blockchain audit trails | Standard DB audit sufficient for MVP |
| Federated learning | Single-tenant model sufficient for v1 |
| OAuth/SSO login | JWT authentication sufficient for MVP |

## Traceability

Which phases cover which requirements. Updated by create-roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 1 | Complete |
| PROC-01 | Phase 1 | Complete |
| PROC-02 | Phase 1 | Complete |
| PROC-03 | Phase 1 | Complete |
| PROC-04 | Phase 1 | Complete |
| PROC-05 | Phase 1 | Complete |
| UPLD-01 | Phase 2 | Pending |
| UPLD-02 | Phase 2 | Pending |
| UPLD-03 | Phase 2 | Pending |
| UPLD-04 | Phase 2 | Pending |
| UPLD-05 | Phase 2 | Pending |
| UPLD-06 | Phase 2 | Pending |
| EXTR-01 | Phase 2 | Pending |
| EXTR-02 | Phase 2 | Pending |
| EXTR-03 | Phase 2 | Pending |
| EXTR-04 | Phase 2 | Pending |
| EXTR-05 | Phase 2 | Pending |
| EXTR-06 | Phase 2 | Pending |
| EXTR-07 | Phase 2 | Pending |
| EXTR-08 | Phase 2 | Pending |
| EXTR-09 | Phase 2 | Pending |
| EXTR-10 | Phase 2 | Pending |
| VALD-01 | Phase 3 | Pending |
| VALD-02 | Phase 3 | Pending |
| VALD-03 | Phase 3 | Pending |
| VALD-04 | Phase 3 | Pending |
| VALD-05 | Phase 3 | Pending |
| VALD-06 | Phase 3 | Pending |
| VALD-07 | Phase 3 | Pending |
| VALD-08 | Phase 3 | Pending |
| VALD-09 | Phase 3 | Pending |
| RAG-01 | Phase 4 | Pending |
| RAG-02 | Phase 4 | Pending |
| RAG-03 | Phase 4 | Pending |
| RAG-04 | Phase 4 | Pending |
| RAG-05 | Phase 4 | Pending |
| RAG-06 | Phase 4 | Pending |
| API-01 | Phase 5 | Complete |
| API-02 | Phase 5 | Complete |
| API-03 | Phase 5 | Complete |
| API-04 | Phase 5 | Complete |
| API-05 | Phase 5 | Complete |
| API-06 | Phase 5 | Complete |
| API-07 | Phase 5 | Complete |
| FIND-01 | Phase 5 | Complete |
| FIND-02 | Phase 5 | Complete |
| FIND-03 | Phase 5 | Complete |
| FIND-04 | Phase 5 | Complete |
| FIND-05 | Phase 5 | Complete |
| FIND-06 | Phase 5 | Complete |
| FIND-07 | Phase 5 | Complete |
| FIND-08 | Phase 5 | Complete |
| FIND-09 | Phase 5 | Complete |
| REPT-01 | Phase 6 | Pending |
| REPT-02 | Phase 6 | Pending |
| REPT-03 | Phase 6 | Pending |
| REPT-04 | Phase 6 | Pending |
| REPT-05 | Phase 6 | Pending |
| REPT-06 | Phase 6 | Pending |
| AUDT-01 | Phase 6 | Pending |
| AUDT-02 | Phase 6 | Pending |
| AUDT-03 | Phase 6 | Pending |
| AUDT-04 | Phase 6 | Pending |
| AUDT-05 | Phase 6 | Pending |
| AUDT-06 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 61 total
- Mapped to phases: 61
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-15*
*Last updated: 2026-01-16 after Phase 5 completion*
