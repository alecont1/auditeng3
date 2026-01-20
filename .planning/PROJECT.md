# AuditEng

## Current State

**Shipped:** v2.0 Web Dashboard (2026-01-20)
**Codebase:** ~38,000 LOC across 182 files (Python backend + TypeScript frontend)
**Tech stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Dramatiq, PostgreSQL, Redis, Claude API, React 18, Vite, Tailwind, shadcn/ui, TanStack Query, Cloudflare R2

## What This Is

Sistema de auditoria automatizada de relatórios de comissionamento elétrico para data centers. Usa IA (Claude) para extrair dados estruturados de PDFs/imagens e código Python para validar contra normas técnicas (NETA, IEEE, Microsoft CxPOR), gerando findings categorizados por severidade com aprovação/reprovação automática.

## Core Value

**"IA extrai, código valida"** — Extração com IA + validação determinística garante reprodutibilidade, explicabilidade e rastreabilidade de cada finding.

## Requirements

### Validated

- ✓ FastAPI backend with health checks and error handling — v1.0
- ✓ SQLAlchemy 2.0 models with Alembic migrations — v1.0
- ✓ Dramatiq job queue with Redis for background processing — v1.0
- ✓ File upload API (PDF up to 50MB, images) — v1.0
- ✓ AI extraction with Instructor + Claude for 3 test types — v1.0
- ✓ Confidence scoring and retry logic — v1.0
- ✓ Deterministic validation against NETA/IEEE standards — v1.0
- ✓ Multi-standard profiles (NETA, Microsoft) with audit traceability — v1.0
- ✓ JWT authentication with OAuth2 flow — v1.0
- ✓ Rate limiting (10 req/min per user) — v1.0
- ✓ Finding generation with severity levels — v1.0
- ✓ Compliance score and verdict computation — v1.0
- ✓ PDF report generation with ReportLab — v1.0
- ✓ Audit trail with rule-level tracking — v1.0
- ✓ OpenAPI/Swagger documentation — v1.0

### Active

(None — awaiting next milestone planning)

### Out of Scope

- App mobile nativo — foco em web/API primeiro
- Integração com sistemas externos (Procore, etc) — MVP standalone
- Multi-idioma — inglês apenas para MVP
- Frontend web completo — API-first, UI básica
- RAG pipeline — standards are finite, hard-coded thresholds suffice for v1

## Context

**Problema:** Engenheiros de comissionamento auditam manualmente centenas de relatórios (15-30 min cada), com alta taxa de erro humano (15%) e sem padronização de critérios.

**Solução:** Automação reduz tempo para 2 min/relatório, taxa de erro para 2%, e aumenta throughput 8x.

**Especificação completa:** Documentação detalhada disponível em:
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/company/` — Visão e produto
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/specs/` — Arquitetura e API
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/knowledge/` — Regras de validação e normas
- `/mnt/c/Users/xande/OneDrive/Documentos/auditenga/.claude/team/` — Personas de agentes

## Constraints

- **Stack**: Python + FastAPI + Instructor + Pydantic v2 + SQLAlchemy 2.0 + PostgreSQL + Redis
- **AI**: Claude Sonnet 4 via Instructor
- **Validation**: 100% determinística
- **Files**: Max 50MB por PDF
- **Deploy**: Railway/Render

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fresh start (não usar código existente) | Specs bem documentados, código existente incompleto | ✓ Good |
| Python-only (sem TypeScript) | Instructor, melhor ecossistema de IA, tipagem com Pydantic | ✓ Good |
| Dramatiq over RQ | Better reliability, cleaner API | ✓ Good |
| pgvector deferred | Standards are finite, hard-coded thresholds suffice | ✓ Good |
| Pydantic v2 with StrEnum | Type safety, JSON serialization | ✓ Good |
| SQLAlchemy 2.0 async | Modern patterns, better performance | ✓ Good |
| BaseValidator pattern | Consistent validation, easy to extend | ✓ Good |
| python-jose for JWT | Better algorithm support than PyJWT | ✓ Good |
| ReportLab for PDF | Minimal dependencies, engineer-focused | ✓ Good |
| Append-only audit logs | Compliance requirement, simple implementation | ✓ Good |

---
*Last updated: 2026-01-16 after v1.0 milestone*
