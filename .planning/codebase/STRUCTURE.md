# Directory Structure

*Last updated: 2026-01-15*

## Repository Layout

```
/home/xande/
├── auditeng/lop-agx/          # Primary TypeScript monorepo
├── auditor/                    # Parallel TypeScript implementation
└── audit/audit/               # Python FastAPI backend
```

## TypeScript Monorepo (auditeng/lop-agx)

```
auditeng/lop-agx/
├── apps/
│   ├── api/                   # Hono backend API
│   │   ├── src/
│   │   │   ├── index.ts       # Server entry point
│   │   │   ├── lib/           # Shared utilities
│   │   │   │   ├── prisma.ts  # Database client
│   │   │   │   ├── jwt.ts     # Token handling
│   │   │   │   ├── password.ts
│   │   │   │   ├── stripe.ts
│   │   │   │   ├── rate-limiter.ts
│   │   │   │   └── audit-log.ts
│   │   │   └── modules/       # Feature modules
│   │   │       ├── auth/
│   │   │       │   ├── auth.routes.ts
│   │   │       │   ├── auth.service.ts
│   │   │       │   └── auth.middleware.ts
│   │   │       ├── users/
│   │   │       ├── companies/
│   │   │       ├── analysis/
│   │   │       ├── tokens/
│   │   │       ├── audit/
│   │   │       ├── ai/
│   │   │       │   ├── extractors/
│   │   │       │   ├── validators/
│   │   │       │   ├── prompts/
│   │   │       │   └── types/
│   │   │       └── rag/
│   │   ├── prisma/
│   │   │   ├── schema.prisma  # Database schema
│   │   │   └── migrations/
│   │   └── package.json
│   │
│   └── web/                   # React frontend
│       ├── src/
│       │   ├── main.tsx       # App entry point
│       │   ├── App.tsx        # Route definitions
│       │   ├── lib/
│       │   │   ├── api.ts     # REST client
│       │   │   ├── auth.tsx   # Auth context
│       │   │   └── utils.ts
│       │   ├── pages/         # Route components
│       │   │   ├── LoginPage.tsx
│       │   │   ├── DashboardPage.tsx
│       │   │   ├── NewAnalysisPage.tsx
│       │   │   ├── AnalysisDetailPage.tsx
│       │   │   ├── HistoryPage.tsx
│       │   │   ├── TokensPage.tsx
│       │   │   ├── settings/
│       │   │   └── super-admin/
│       │   └── components/
│       │       ├── layout/
│       │       │   ├── MainLayout.tsx
│       │       │   └── Breadcrumbs.tsx
│       │       ├── ui/
│       │       │   └── Modal.tsx
│       │       ├── ProtectedRoute.tsx
│       │       └── InviteUserModal.tsx
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── package.json
│
├── packages/                  # Shared packages (future)
├── pnpm-workspace.yaml
├── package.json
├── .env.example
└── README.md
```

## Python Backend (audit/audit)

```
audit/audit/
├── app/
│   ├── main.py                # FastAPI app factory
│   ├── config.py              # Pydantic Settings
│   ├── api/
│   │   └── v1/
│   │       ├── router.py      # Router aggregation
│   │       ├── analyze.py     # PDF upload endpoint
│   │       ├── auth.py        # Authentication
│   │       ├── tasks.py       # Task status/results
│   │       ├── admin.py       # Admin operations
│   │       └── deps.py        # Dependency injection
│   ├── core/
│   │   ├── agents/            # AI extraction (empty)
│   │   ├── validators/        # Rule enforcement (empty)
│   │   └── rules/             # Standards (empty)
│   ├── schemas/
│   │   ├── base.py            # Enums (TaskStatus, Verdict, Severity)
│   │   ├── extraction.py      # AI extraction schemas
│   │   ├── findings.py        # Finding data models
│   │   └── api.py             # API request/response
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── session.py         # Async session factory
│   │   └── repositories/
│   │       ├── users.py
│   │       └── tasks.py
│   ├── services/              # External services (empty)
│   ├── worker/                # Background jobs (empty)
│   └── utils/
├── alembic/
│   ├── env.py
│   └── versions/              # Migrations (empty)
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docker/
│   └── Dockerfile
├── pyproject.toml
└── alembic.ini
```

## Key Locations

### Configuration Files
- `auditeng/lop-agx/.env.example` - Environment template
- `auditeng/lop-agx/apps/api/prisma/schema.prisma` - Database schema
- `auditeng/lop-agx/apps/web/vite.config.ts` - Build config
- `audit/audit/app/config.py` - Python settings

### Entry Points
- `auditeng/lop-agx/apps/web/src/main.tsx` - React app
- `auditeng/lop-agx/apps/api/src/index.ts` - Hono server
- `audit/audit/app/main.py` - FastAPI server

### Business Logic
- `auditeng/lop-agx/apps/api/src/modules/` - TypeScript modules
- `audit/audit/app/core/` - Python core logic

### Database
- `auditeng/lop-agx/apps/api/prisma/` - Prisma schema & migrations
- `audit/audit/app/db/` - SQLAlchemy models & repositories

### AI Integration
- `auditeng/lop-agx/apps/api/src/modules/ai/` - Claude extractors
- `auditeng/lop-agx/apps/api/src/modules/rag/` - RAG pipeline
- `audit/audit/app/core/agents/` - Python AI agents (planned)

## Naming Conventions

### Files
- **React components**: `PascalCase.tsx` (e.g., `InviteUserModal.tsx`)
- **TypeScript modules**: `kebab-case.ts` (e.g., `auth.routes.ts`)
- **Python modules**: `snake_case.py` (e.g., `base.py`)

### Directories
- **Feature modules**: lowercase (`auth/`, `users/`, `analysis/`)
- **Layer folders**: lowercase (`lib/`, `components/`, `pages/`)
