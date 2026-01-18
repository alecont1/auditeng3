# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-17)

**Core value:** "IA extrai, codigo valida" — AI extraction + deterministic validation ensures reproducibility, explainability, and traceability of every finding.
**Current focus:** v2.0 Web Dashboard — React frontend for AuditEng

## Current Position

Phase: 13 of 14 (Backend Extensions)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-01-18 — Completed 13-01-PLAN.md (List Analyses Endpoint)

Progress: ███████████░░░░░░░░░ 15/19 plans (79%)

## Milestone v2.0 Overview

**Goal:** Interface web para engenheiros revisarem e aprovarem análises automatizadas.

**Stack:** React 18 + Vite + Tailwind + shadcn/ui + TanStack Query

**Phases:**
| Phase | Focus | Plans | Status |
|-------|-------|-------|--------|
| 07 | Setup & Auth | 3 | Complete (3/3) |
| 08 | Layout & Components | 2 | Complete (2/2) |
| 09 | Upload | 2 | Complete (2/2) |
| 10 | Dashboard | 2 | Complete (2/2) |
| 11 | Details & Review | 3 | Complete (3/3) |
| 12 | Reports & Audit | 2 | Complete (2/2) |
| 13 | Backend Extensions | 2 | In Progress (1/2) |
| 14 | Polish & Deploy | 3 | Pending |

## Performance Metrics

**v1.0 Milestone (Shipped):**
- Total plans completed: 27
- Total phases: 6
- Duration: 2 days (2026-01-15 → 2026-01-16)
- Codebase: 13,142 LOC Python, 92 files

## Accumulated Context

### Decisions (v2.0)

| Decision | Rationale | Status |
|----------|-----------|--------|
| React + Vite over Next.js | SPA sufficient, simpler setup, no SSR needed | Confirmed |
| shadcn/ui components | Copy-paste ownership, Tailwind native, no lock-in | Confirmed |
| TanStack Query | Superior caching, refetching, simpler than Redux | Confirmed |
| Tailwind v3 over v4 | shadcn/ui compatibility requires v3 | 07-01 |
| CSS variables theming | Enables light/dark mode switching | 07-01 |
| localStorage for token | Simple for SPA, no SSR needed | 07-02 |
| Custom auth:logout event | Decouples API interceptor from React context | 07-02 |
| React Router v6 | Modern declarative routing with Routes/Route | 07-03 |
| ProtectedRoute pattern | Wrapper checks isAuthenticated, shows loading while checking | 07-03 |
| Fixed sidebar 240px | Standard SaaS app shell width, overlay on mobile | 08-01 |
| NavLink for navigation | Uses react-router-dom NavLink for automatic active state | 08-01 |
| MainLayout wrapper pattern | Protected routes wrapped in MainLayout for consistent shell | 08-01 |
| sonner for toasts | Lightweight, shadcn-compatible, simple API | 08-02 |
| Class ErrorBoundary | React requires class components for componentDidCatch | 08-02 |
| Native drag-drop events | No external library (react-dropzone), uses HTML5 API | 09-01 |
| File validation before callback | Validate type/size before passing file to parent | 09-01 |
| TanStack Query for API | Mutations, polling, caching via react-query | 09-02 |
| 2-second polling interval | Balance between responsiveness and server load | 09-02 |
| Services layer pattern | API calls in services/, wrapped by hooks | 09-02 |
| Status badge colors | pending=amber, completed=green, failed=red | 10-01 |
| Verdict badge colors | approved=green, rejected=red, needs_review=amber (outline) | 10-01 |
| Compliance score thresholds | >=90% green, >=70% amber, <70% red | 10-01 |
| Filter "all" value | undefined represents no filter (mapped from "all" string) | 10-02 |
| Combined sort dropdown | Single dropdown combines sort field and direction | 10-02 |
| Approximate stats | QuickStats computed from current page until backend stats endpoint | 10-02 |
| useState over useMutation for download | Download triggers file save, not cache update | 12-01 |
| Header positioning for download | Logically separate from approve/reject actions | 12-01 |
| Disabled via verdict check | Backend returns 400 for incomplete analyses | 12-01 |
| Client-side filtering for audit | ~100 events max, simpler than round-tripping to server | 12-02 |
| 30s stale time for audit | Audit trails don't change often, reduces API calls | 12-02 |
| Intl.DateTimeFormat for timestamps | Native browser API, no external dependency | 12-02 |
| Color-coded event categories | Visual categorization: blue=extraction, green=validation, amber=finding, purple=review | 12-02 |

### API Endpoints Needed

Backend extensions (Phase 13):
- `GET /api/analyses` — List user's analyses (paginated, filterable)
- `PUT /api/analyses/{id}/approve` — Mark analysis as approved
- `PUT /api/analyses/{id}/reject` — Mark as rejected with reason

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-01-18
Stopped at: Completed 13-01-PLAN.md (List Analyses Endpoint)
Resume file: None

## Next Action

Execute next plan in Phase 13:
```
/gsd:execute-plan .planning/phases/13-backend-extensions/13-02-PLAN.md
```
