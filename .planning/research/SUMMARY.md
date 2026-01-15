# Research Summary: AuditEng

> Synthesized from domain research conducted January 2026
> Purpose: Inform roadmap and architecture decisions

---

## Executive Summary

Research confirms that the "AI extrai, código valida" principle is the industry-recommended pattern. Key findings indicate that **Instructor + Pydantic** is the standard for structured LLM extraction, **pgvector** simplifies RAG by keeping vectors in PostgreSQL, and **Dramatiq** provides better reliability than RQ for background jobs. The most critical pitfall to avoid is treating AI confidence as ground truth—calibration is essential.

---

## Stack Recommendations

### Confirmed Choices (Aligned with PROJECT.md)

| Component | Recommendation | Confidence |
|-----------|---------------|------------|
| **LLM Extraction** | Instructor 1.7+ with Claude | High |
| **Schema Validation** | Pydantic v2.10+ | High |
| **Web Framework** | FastAPI 0.115+ | High |
| **Database** | PostgreSQL 16+ with SQLAlchemy 2.0 async | High |
| **Caching** | Redis 7+ | High |

### Refinements from Research

| Component | Original Plan | Research Recommendation | Reason |
|-----------|--------------|------------------------|--------|
| **Vector Store** | Not specified | **pgvector** (PostgreSQL extension) | Simplifies infrastructure, ACID compliance, hybrid SQL+vector queries |
| **Task Queue** | Redis + RQ | **Dramatiq** (or RQ if simpler needed) | Better reliability (acks on completion), 10x faster than RQ |
| **PDF Processing** | Not specified | **PyMuPDF** (native) + **Claude Vision** (complex) | Best speed/quality balance; Claude handles scanned docs natively |
| **Embeddings** | Not specified | **text-embedding-3-small** (OpenAI) | Cost-effective, 1536 dimensions, proven quality |
| **Chunking** | Not specified | 256-512 tokens with 10-20% overlap, semantic boundaries | Research-backed optimal parameters |

### Recommended requirements.txt

```
# Web Framework
fastapi[standard]>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
pydantic-settings>=2.6.0

# Database
sqlalchemy[asyncio]>=2.0.36
asyncpg>=0.29.0
alembic>=1.14.0
pgvector>=0.3.0

# LLM & Extraction
instructor>=1.7.0
anthropic>=0.40.0
openai>=1.55.0  # for embeddings

# PDF Processing
pymupdf>=1.24.0
pymupdf4llm>=0.0.17
pdf2image>=1.17.0
Pillow>=10.0.0

# RAG & Text Processing
langchain-text-splitters>=0.3.0
tiktoken>=0.8.0

# Caching & Queue
redis>=5.2.0
dramatiq[redis]>=1.17.0

# Utilities
python-dotenv>=1.0.0
httpx>=0.28.0
tenacity>=9.0.0
```

---

## Feature Prioritization

### MVP Must-Have (Table Stakes)

1. **Core Extraction** - OCR, table extraction, image processing for 3 test types
2. **Standard-Based Validation** - NETA/IEEE threshold checks with deterministic rules
3. **Severity Classification** - CRITICAL, MAJOR, MINOR, INFO (industry standard)
4. **Confidence Scoring** - Per-field scores with configurable thresholds (0.70-0.95)
5. **PDF Report Generation** - Findings summary with evidence
6. **Complete Audit Trail** - Timestamped logs for compliance
7. **REST API** - Well-documented endpoints

### Near-Term Differentiators (v1.x)

1. **Human-in-the-Loop (HITL)** - Smart review queues push accuracy from 70% to 95%+
2. **Appeal/Override Mechanism** - Structured dispute with justification capture
3. **Correction Feedback Loop** - Captured corrections improve future extractions
4. **Equipment-Specific Validation** - Rules per PANEL, UPS, ATS, GEN, XFMR
5. **Dashboard Analytics** - Trend visualization and risk heat maps

### Future Vision (v2.0+)

1. **Agentic Processing** - End-to-end automation (25% of companies piloting)
2. **Cross-Document Intelligence** - Link related reports
3. **Predictive Analytics** - Proactive issue detection
4. **Explainable AI** - Decision rationale (EU AI Act driver)

---

## Architecture Implications

### Core Principle Validated

The research strongly supports the **"AI extrai, código valida"** principle:

```
┌─────────────────────────────────────────────────────────────┐
│ Document → AI Extraction (non-deterministic, logged)        │
│                     ↓                                       │
│ Structured Data → Code Validation (deterministic, testable) │
│                     ↓                                       │
│ Validated Result → Audit Trail + Persistence                │
└─────────────────────────────────────────────────────────────┘
```

### Three-Layer Validation

1. **Structural Validation** (Pydantic) - Types, formats, required fields
2. **Extraction Validation** (Instructor) - Confidence scores, retry logic
3. **Business Rule Validation** (Python) - NETA/IEEE compliance, cross-field checks

### RAG Integration Pattern

```
Offline: Standards → Chunk → Embed → Index (pgvector)
Online:  Validation Query → Retrieve Context → Apply Rules
```

Key insight: "The LLM is not the bottleneck - your retrieval is." Hybrid search (vector + keyword) provides best results.

### Background Processing

```python
# Dramatiq pattern for reliability
@dramatiq.actor(max_retries=3, min_backoff=1000)
def process_commissioning_report(report_id: int):
    # 1. Extract with Claude + Instructor
    # 2. Get relevant standards via RAG
    # 3. Validate deterministically
    # 4. Store with audit trail
```

---

## Critical Pitfalls to Avoid

### Top 5 Risks for AuditEng

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Treating confidence as ground truth** | False approvals/rejections | Calibrate scores on held-out data; per-field thresholds |
| **Poor PDF parsing quality** | All downstream quality capped | Test on production diversity; use PyMuPDF + Claude Vision |
| **No feedback loop** | Same errors repeat forever | Capture corrections → retrain/improve |
| **Hard-coded thresholds** | Tech debt, outdated standards | Externalize to config; link to standard sources |
| **No reprocessing capability** | Can't fix historical extractions | Retain originals; idempotent pipelines |

### Domain-Specific Risks

1. **Thermal Image Extraction** - Temperature data is in color, not text; need multimodal
2. **Calibration Certificate Validation** - Expiration dates, traceability chain critical
3. **NETA/IEEE Version Mismatch** - Standards update frequently (NETA ATS-2025 released Feb 2025)
4. **Unit Inconsistencies** - Must extract and normalize units with values
5. **Multi-Page Continuity** - Equipment ID must track across pages

---

## Roadmap Implications

### Phase Sequencing Recommendations

**Phase 1: Foundation** (Do First)
- Data models with Pydantic v2
- Database schema with SQLAlchemy 2.0 async
- API skeleton with FastAPI
- Dramatiq job queue setup
- Basic audit logging

**Phase 2: Extraction Pipeline** (Core Value)
- Instructor + Claude integration
- PDF processing with PyMuPDF + Claude Vision
- Structured extraction for 3 test types
- Confidence scoring per field
- Error handling and retry logic

**Phase 3: Validation Engine** (Deterministic Core)
- Validation rule framework (code + config)
- NETA/IEEE threshold rules
- Cross-field validation
- Severity classification
- Finding generation

**Phase 4: RAG Pipeline** (Intelligence Layer)
- pgvector setup
- Standards document ingestion
- Semantic chunking (256-512 tokens)
- Hybrid search (vector + keyword)
- Context injection into validation

**Phase 5: API & Integration**
- Complete REST API
- File upload/download
- Status polling / webhooks
- Authentication + authorization
- Rate limiting

**Phase 6: Reporting & Quality**
- PDF report generation
- Dashboard basics
- Quality monitoring
- Human review queue (HITL)
- Feedback capture

### Risk Reduction Strategies

1. **Start with simplest test type** (Grounding) before complex (Thermography)
2. **Build evaluation harness early** - Golden test sets with known answers
3. **Implement audit logging from day one** - Never retrofit
4. **Pin all dependencies** - Reproducible builds
5. **Test on real production PDFs** - Not just clean samples

---

## Key Metrics Targets

| Metric | Target | Industry Benchmark |
|--------|--------|-------------------|
| Field extraction accuracy | >95% | 90-95% with HITL |
| Straight-through processing | >70% | 70-95% typical |
| False positive rate | <5% | Domain varies |
| Processing time | <30 sec/page | Depends on complexity |
| Appeal/override rate | <10% | Indicates validation accuracy |

---

## Sources & References

Full source citations available in individual research documents:
- `STACK.md` - 30+ sources on stack choices
- `FEATURES.md` - 25+ sources on feature landscape
- `ARCHITECTURE.md` - 20+ sources on architecture patterns
- `PITFALLS.md` - 25+ sources on common failures

---

*Research synthesized: January 2026*
*For: AuditEng - Sistema de Auditoria Automatizada de Relatórios de Comissionamento Elétrico*
