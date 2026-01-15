# Architecture

*Last updated: 2026-01-15*

## Pattern Overview

**Polyrepo with Multiple Specialized Services**

The codebase consists of interconnected projects:
1. **auditeng/lop-agx** - TypeScript monorepo (React frontend + Hono API)
2. **audit** - Python FastAPI backend for AI-powered validation
3. **auditor** - Parallel TypeScript implementation (similar to lop-agx)

## Architectural Style

### TypeScript API (Hono)
**Modular REST API with Feature-based Modules**

Each module is self-contained with routes, services, and middleware:
```
src/modules/
├── auth/          # Authentication & authorization
├── analysis/      # PDF analysis processing
├── users/         # User management
├── companies/     # Company management
├── tokens/        # Token balance system
├── ai/            # AI extraction logic
└── rag/           # Retrieval-augmented generation
```

### Python API (FastAPI)
**Layered Architecture with Repository Pattern**

```
app/
├── api/v1/        # HTTP API layer
├── core/          # Business logic (agents, validators, rules)
├── db/            # Data access layer
├── schemas/       # Data contracts (Pydantic)
├── services/      # External integrations
└── worker/        # Background jobs
```

## Layers

### Presentation Layer
- **Web**: React SPA with React Router (`auditeng/lop-agx/apps/web/src/App.tsx`)
- **API**: Hono routes (`auditeng/lop-agx/apps/api/src/modules/*/routes.ts`)
- **FastAPI**: REST endpoints (`audit/audit/app/api/v1/*.py`)

### Business Logic Layer
- **TypeScript Services**: `auditeng/lop-agx/apps/api/src/modules/*/*.service.ts`
- **Python Core**: `audit/audit/app/core/` (agents, validators, rules)

### Data Access Layer
- **Prisma ORM**: `auditeng/lop-agx/apps/api/src/lib/prisma.ts`
- **SQLAlchemy**: `audit/audit/app/db/repositories/*.py`

## Data Flow

### Analysis Request Lifecycle (TypeScript)
```
1. User Upload (React) → POST /api/analysis
2. Token Balance Check → getTokenBalance()
3. Analysis Created → Prisma database
4. AI Extraction → modules/ai/extractors/claude-extractor.ts
5. Validation → modules/ai/validators/
6. RAG Enhancement → modules/rag/rag.service.ts
7. Results Stored → Prisma database
8. Frontend Update → Dashboard display
```

### Analysis Request Lifecycle (Python)
```
1. PDF Upload → POST /api/v1/analyze
2. File Validation + Storage
3. Task Created (status=QUEUED)
4. Background Worker (Redis/RQ) [Not implemented]
5. AI Extraction → core/agents/
6. Validation → core/validators/
7. Score Calculation → SEVERITY_PENALTIES
8. Verdict Determination
9. Results Stored → Task model
```

## Key Abstractions

### TypeScript API
- **Module Routes**: Feature-scoped Hono routers
- **Services**: Business logic encapsulation
- **Middleware**: Cross-cutting concerns (auth, rate-limit)
- **Prisma Models**: Type-safe database access

### Python API
- **Repository Pattern**: `TaskRepository`, `UserRepository`
- **Pydantic Schemas**: Type-safe data contracts
- **FastAPI Dependencies**: Injection for auth, database
- **Enums**: Domain language (`TaskStatus`, `Verdict`, `Severity`)

## Entry Points

| Project | Entry | Port | Purpose |
|---------|-------|------|---------|
| Web | `apps/web/src/main.tsx` | 3000 | React SPA |
| TypeScript API | `apps/api/src/index.ts` | 3001 | Hono server |
| Python API | `audit/audit/app/main.py` | 8000 | FastAPI server |

## Module Boundaries

### TypeScript Modules
- **auth**: JWT tokens, login/logout, password management
- **users**: User CRUD, invitations
- **companies**: Company management
- **analysis**: PDF upload, processing, results
- **tokens**: Balance checking, transactions
- **ai**: Claude API integration, extraction, validation
- **rag**: Embeddings, criteria indexing

### Python Modules
- **api/v1**: HTTP endpoints
- **core/agents**: AI extraction
- **core/validators**: Rule enforcement
- **core/rules**: NETA/Microsoft standards
- **db**: Database models and repositories
- **schemas**: Request/response contracts

## Cross-cutting Concerns

- **Authentication**: JWT middleware (`requireAuth`)
- **Authorization**: Role-based access (`requireRole`)
- **Rate Limiting**: Per-IP throttling (`rate-limiter.ts`)
- **Audit Logging**: Action tracking (`audit-log.ts`)
- **Error Handling**: Consistent JSON responses
