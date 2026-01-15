# AuditEng Technology Stack Research (2025-2026)

> Research conducted: January 2026
> Purpose: Best practices and recommendations for AI-powered document validation/extraction systems

## Table of Contents
1. [Structured LLM Extraction](#1-structured-llm-extraction-with-python)
2. [PDF/Image Processing](#2-pdfimage-processing-libraries)
3. [RAG Stack for Technical Documents](#3-rag-stack-for-technical-document-retrieval)
4. [Background Job Queues](#4-background-job-queues)
5. [Async Python Web Frameworks](#5-async-python-web-framework-landscape)
6. [Recommended Stack Summary](#6-recommended-stack-summary)

---

## 1. Structured LLM Extraction with Python

### Recommendation: **Instructor** (Primary) + Consider **PydanticAI** for Agent Workflows

**Instructor** is the current industry standard with 3M+ monthly downloads and 11k+ GitHub stars. It provides:
- Type-safe data extraction with Pydantic v2 integration
- Automatic validation, retries, and streaming support
- Support for 15+ LLM providers including Anthropic Claude
- Multimodal support (images, PDFs, audio)

```python
# Instructor with Claude example
import instructor
from pydantic import BaseModel

class ExtractedData(BaseModel):
    equipment_id: str
    test_result: float
    pass_fail: bool

client = instructor.from_provider("anthropic/claude-sonnet-4-20250514")
result = client.create(
    response_model=ExtractedData,
    messages=[{"role": "user", "content": "Extract from: Motor M-101 tested at 450V, result: PASS"}]
)
```

**Version recommendation**: `instructor>=1.7.0`

### Alternatives Considered

| Library | Best For | Trade-offs |
|---------|----------|------------|
| **PydanticAI** | Agent workflows, observability, production dashboards | More complex, overkill for simple extraction |
| **BAML** | Cross-language APIs, strict contracts | Contract-first approach, code generation overhead |
| **Mirascope** | Complex workflows, prompt chaining | Wider scope than needed |
| **Outlines** | Local models, constrained generation | Only for self-hosted models |
| **LangExtract** (Google) | Source grounding, traceability | Newer, less mature ecosystem |

**Key insight**: For AuditEng's use case (structured extraction from commissioning reports), Instructor is the optimal choice. Claude models don't natively support `response_format` like OpenAI, but Instructor handles this via tool-based structured output with schema validation.

---

## 2. PDF/Image Processing Libraries

### Recommendation: **PyMuPDF** (primary) + **Claude Vision** (for complex layouts)

### Library Comparison (2025 Benchmarks)

| Library | Speed | Best For |
|---------|-------|----------|
| **pypdfium2** | 0.003s | Pure speed, basic text |
| **pypdf** | 0.024s | Reliable extraction, no C deps |
| **pdfplumber** | 0.10s | Table extraction |
| **unstructured** | 1.29s | RAG workflows, semantic chunks |
| **marker-pdf** | 12s | Layout-perfect markdown |

### Recommended Approach for AuditEng

1. **Native PDFs (digital text)**: Use **PyMuPDF** (`pymupdf4llm`)
   - Fast extraction with table detection
   - Good layout preservation
   - Version: `pymupdf>=1.24.0`, `pymupdf4llm>=0.0.17`

2. **Scanned PDFs/Images**: Use **Claude Vision API directly**
   - Claude processes PDFs as image + text combination per page
   - Constraints: Max 100 pages, 32MB per request
   - Cost: 1,500-3,000 tokens per page

3. **For RAG ingestion**: Use **Unstructured**
   - Semantic chunking with labeled elements (Title, NarrativeText, Table)
   - Version: `unstructured>=0.16.0`

```python
# Claude Vision for complex commissioning reports
import anthropic
import base64

client = anthropic.Anthropic()
with open("report.pdf", "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
            {"type": "text", "text": "Extract all test results from this commissioning report."}
        ]
    }]
)
```

### Image Processing for Equipment Photos

For equipment photos in commissioning reports:
- **pdf2image** + **Pillow**: Convert PDF pages to images (max 2000x2000)
- **Claude Vision**: Interpret charts, diagrams, equipment photos
- Version: `pdf2image>=1.17.0`, `Pillow>=10.0.0`

---

## 3. RAG Stack for Technical Document Retrieval

### Recommendation: **pgvector** + **text-embedding-3-small** + **Semantic Chunking**

Given AuditEng's existing PostgreSQL stack, pgvector is the optimal choice for vector storage.

### Vector Database: pgvector

**Why pgvector for AuditEng:**
- Already using PostgreSQL (no additional infrastructure)
- ACID compliance for regulatory documents
- Hybrid queries (combine vector search with SQL filters)
- Production-ready with proper indexing

**Setup:**
```sql
-- Enable extension
CREATE EXTENSION vector;

-- Create table with vector column
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embedding dimension
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast approximate search
CREATE INDEX ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Python integration:**
```python
# pgvector with SQLAlchemy 2.0
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import mapped_column

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
    embedding: Mapped[list] = mapped_column(Vector(1536))
```

**Version**: `pgvector>=0.3.0` (Python), PostgreSQL extension `v0.8.x`

### Embedding Models

| Model | Dimensions | Best For | Cost |
|-------|------------|----------|------|
| **text-embedding-3-small** | 1536 | General purpose, cost-effective | $0.02/1M tokens |
| **text-embedding-3-large** | 3072 | Maximum accuracy | $0.13/1M tokens |
| **voyage-3-lite** | 1024 | Technical/legal documents | Competitive |
| **BGE-M3** | 1024 | Open source, multilingual | Free |

**Recommendation**: Start with `text-embedding-3-small` for AuditEng. Consider `voyage-3` if domain-specific accuracy becomes critical.

### Chunking Strategy for Technical Standards

**Optimal parameters for NETA/IEEE documents:**
- **Chunk size**: 256-512 tokens (research shows this is the sweet spot)
- **Overlap**: 10-20% (50-100 tokens for 500-token chunks)
- **Strategy**: Semantic chunking preserving section boundaries

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " "],  # Preserve paragraphs
    length_function=len,
)

# For technical standards, consider section-aware chunking
# Keep tables intact, preserve numbered lists
```

**Key insight**: A well-built RAG with a smaller model can outperform raw GPT-4 by 31% on accuracy for technical document Q&A because retrieval provides exactly the right context.

### Production Configuration

```python
# pgvector production settings
PGVECTOR_CONFIG = {
    "index_type": "hnsw",
    "m": 16,  # connections per layer
    "ef_construction": 64,  # build-time accuracy
    "ef_search": 40,  # query-time accuracy (tune based on recall targets)
}

# Autovacuum for vector tables
# SET autovacuum_vacuum_scale_factor = 0.05
# SET autovacuum_analyze_scale_factor = 0.02
```

---

## 4. Background Job Queues

### Recommendation: **Dramatiq** (Primary) or **RQ** (Simpler alternative)

### Comparison Matrix

| Feature | Celery | Dramatiq | RQ | ARQ |
|---------|--------|----------|-----|-----|
| **Performance** | Good | Excellent (10x RQ) | Moderate | Poor |
| **Complexity** | High | Medium | Low | Low |
| **Reliability** | Good* | Excellent | Good | Moderate |
| **Brokers** | Redis, RabbitMQ, more | Redis, RabbitMQ | Redis only | Redis only |
| **Async Support** | Limited | Good | Limited | Native |

*Celery acks tasks on pull by default (bad default); Dramatiq acks only on completion.

### Recommendation for AuditEng: **Dramatiq**

**Why Dramatiq:**
1. Better message reliability (acks on completion, not on pull)
2. Simpler configuration than Celery
3. Excellent performance in benchmarks
4. Works with Redis (already in AuditEng stack)
5. Good balance of features vs complexity

```python
# Dramatiq setup for AuditEng
import dramatiq
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(url="redis://localhost:6379/0")
dramatiq.set_broker(redis_broker)

@dramatiq.actor(max_retries=3, min_backoff=1000)
def process_commissioning_report(report_id: int):
    """Extract and validate commissioning report."""
    # 1. Fetch PDF from storage
    # 2. Extract with PyMuPDF + Claude
    # 3. Validate against NETA standards
    # 4. Store results
    pass

@dramatiq.actor(queue_name="high-priority")
def validate_against_standards(extraction_id: int, standard: str):
    """Run validation against specific standard."""
    pass
```

**Version**: `dramatiq>=1.17.0`, `dramatiq[redis]`

### Alternative: RQ for Simpler Needs

If complexity must be minimized:
```python
from redis import Redis
from rq import Queue

q = Queue(connection=Redis())
job = q.enqueue(process_commissioning_report, report_id=123)
```

**Version**: `rq>=1.16.0`

### Security Note (2025)

**Never use pickle serialization** - major security vulnerability. Always use JSON:
```python
# Dramatiq (JSON by default)
# Celery: task_serializer = 'json'
```

### Monitoring

- **Dramatiq**: Use `dramatiq-dashboard` or RabbitMQ Management Plugin
- **RQ**: Use `rq-dashboard`
- **Celery**: Use `flower`

---

## 5. Async Python Web Framework Landscape

### Recommendation: **FastAPI** (Production-ready) or **Litestar** (Performance-critical)

### Framework Comparison

| Aspect | FastAPI | Litestar | Starlette |
|--------|---------|----------|-----------|
| **GitHub Stars** | 84k+ | Growing fast | Foundation |
| **Performance** | Excellent | Superior* | Fastest |
| **Ecosystem** | Mature | Growing | Minimal |
| **Learning Curve** | Low | Low-Medium | Medium |
| **OpenAPI** | Built-in | Built-in | Manual |
| **Pydantic** | Tightly coupled | Optional | N/A |

*Litestar uses msgspec (12x faster than Pydantic v2 for serialization)

### Recommendation for AuditEng: **FastAPI**

**Why FastAPI:**
1. Mature ecosystem with extensive documentation
2. Battle-tested in production (OpenAI, Anthropic, Microsoft)
3. Excellent SQLAlchemy 2.0 async integration
4. Large community = easier hiring, more resources
5. Native Pydantic v2 integration (already in AuditEng stack)

```python
# FastAPI with async SQLAlchemy 2.0
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="AuditEng API", version="1.0.0")

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/auditeng",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

@app.post("/reports/", response_model=ReportResponse)
async def create_report(
    report: ReportCreate,
    db: AsyncSession = Depends(get_db)
):
    # Process commissioning report
    pass
```

### When to Consider Litestar

Consider Litestar if:
- Performance is absolutely critical (msgspec is 12x faster)
- You need flexible data validation (supports dataclasses, attrs, msgspec)
- Large codebase benefits from better route organization (Controllers)
- Built-in HTMX support needed

### SQLAlchemy 2.0 Async Best Practices

```python
# requirements.txt
fastapi[standard]>=0.115.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0

# Key configuration
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for async
)

# Alembic async migrations
# alembic init -t async migrations
```

---

## 6. Recommended Stack Summary

### Core Stack for AuditEng

```
┌─────────────────────────────────────────────────────────────┐
│                     AuditEng Architecture                    │
├─────────────────────────────────────────────────────────────┤
│  Web Framework:     FastAPI 0.115+                          │
│  Data Validation:   Pydantic v2.10+                         │
│  LLM Extraction:    Instructor 1.7+ with Claude             │
│  Database:          PostgreSQL 16+ with SQLAlchemy 2.0      │
│  Vector Store:      pgvector 0.8+ (PostgreSQL extension)    │
│  Caching:           Redis 7+ with redis-py async            │
│  Task Queue:        Dramatiq 1.17+ with Redis broker        │
│  PDF Processing:    PyMuPDF 1.24+ / Claude Vision           │
│  Embeddings:        OpenAI text-embedding-3-small           │
│  ASGI Server:       Uvicorn with uvloop                     │
└─────────────────────────────────────────────────────────────┘
```

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

### Key Architecture Decisions

1. **Use pgvector over dedicated vector DB**: Simplifies infrastructure, ACID compliance for regulatory documents, hybrid SQL+vector queries

2. **Use Instructor over raw Claude API**: Type safety, automatic retries, Pydantic integration matches existing stack

3. **Use Dramatiq over Celery**: Better reliability (ack on completion), simpler config, excellent performance

4. **Use FastAPI over Litestar**: Ecosystem maturity, hiring pool, existing team familiarity

5. **Use Claude Vision for complex PDFs**: Native PDF support, handles tables/charts/images in commissioning reports

---

## Sources

### Structured LLM Extraction
- [Instructor Official Documentation](https://python.useinstructor.com/)
- [The Best Library for Structured LLM Output](https://simmering.dev/blog/structured_output/)
- [BAML vs Instructor Comparison](https://www.glukhov.org/post/2025/12/baml-vs-instruct-for-structured-output-llm-in-python/)
- [PydanticAI vs Instructor](https://medium.com/@mahadevan.varadhan/pydanticai-vs-instructor-structured-llm-ai-outputs-with-python-tools-c7b7b202eb23)
- [Instructor with Anthropic Tutorial](https://python.useinstructor.com/integrations/anthropic/)

### PDF/Image Processing
- [I Tested 7 Python PDF Extractors (2025)](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
- [Best Python PDF to Text Libraries (2026)](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/)
- [Claude PDF Support Documentation](https://platform.claude.com/docs/en/build-with-claude/pdf-support)
- [Claude Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision)

### RAG Stack
- [RAG Stack I'd Use Starting from Zero in 2025](https://medium.com/devmap/the-rag-stack-id-use-if-i-were-starting-from-zero-in-2025-and-why-c4b1d67ad859)
- [Chunking Strategies for RAG (Stack Overflow)](https://stackoverflow.blog/2024/12/27/breaking-up-is-hard-to-do-chunking-in-rag-applications/)
- [Best Chunking Strategies for RAG in 2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)
- [pgvector PostgreSQL Guide 2025](https://dbadataverse.com/tech/postgresql/2025/12/pgvector-postgresql-vector-database-guide)
- [pgvector Python GitHub](https://github.com/pgvector/pgvector-python)

### Background Job Queues
- [Python Background Tasks 2025: Celery vs RQ vs Dramatiq](https://devproportal.com/languages/python/python-background-tasks-celery-rq-dramatiq-comparison-2025/)
- [Choosing The Right Python Task Queue](https://judoscale.com/blog/choose-python-task-queue)
- [Python Task Queue Benchmark](https://stevenyue.com/blogs/exploring-python-task-queue-libraries-with-load-test)
- [Dramatiq Motivation](https://dramatiq.io/motivation.html)

### Async Web Frameworks
- [FastAPI vs Litestar 2025](https://medium.com/@rameshkannanyt0078/fastapi-vs-litestar-2025-which-async-python-web-framework-should-you-choose-8dc05782a276)
- [Litestar is Worth a Look](https://www.b-list.org/weblog/2025/aug/06/litestar/)
- [Litestar vs FastAPI (Better Stack)](https://betterstack.com/community/guides/scaling-python/litestar-vs-fastapi/)
- [FastAPI with Async SQLAlchemy 2.0](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)

### Redis & Caching
- [Using Redis with FastAPI (Redis Official)](https://redis.io/tutorials/develop/python/fastapi/)
- [Complete FastAPI Caching Guide](https://blog.greeden.me/en/2025/09/17/blazing-fast-rock-solid-a-complete-fastapi-caching-guide-redis-http-caching-etag-rate-limiting-and-compression/)
- [fastapi-cache GitHub](https://github.com/long2ice/fastapi-cache)
