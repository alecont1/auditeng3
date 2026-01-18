---
phase: 14-polish-deploy
plan: 02
subsystem: ui
tags: [tailwind, responsive, ux, loading-states, error-handling]

# Dependency graph
requires:
  - phase: 14-01
    provides: Testing infrastructure and confidence in component behavior
  - phase: 08-01
    provides: MainLayout and Sidebar base components
  - phase: 10-02
    provides: Dashboard filtering and pagination hooks
provides:
  - Polished loading states with keepPreviousData for pagination
  - User-friendly error messages with specific failure reasons
  - Mobile responsive layout at 768px breakpoint
affects: [14-03-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns: [keepPreviousData for pagination, error message specificity]

key-files:
  modified:
    - web/src/hooks/useAnalyses.ts
    - web/src/pages/LoginPage.tsx
    - web/src/pages/UploadPage.tsx
    - web/src/hooks/useApproveAnalysis.ts
    - web/src/hooks/useRejectAnalysis.ts
    - web/src/components/layout/Sidebar.tsx
    - web/src/components/layout/MainLayout.tsx
    - web/src/index.css

key-decisions:
  - "keepPreviousData for pagination: Prevents table flash during page changes"
  - "768px breakpoint for sidebar collapse: Standard tablet width, matches md: Tailwind prefix"
  - "Error message specificity: Distinguish network errors from auth errors for actionable feedback"

patterns-established:
  - "keepPreviousData pattern: Use for any paginated list to maintain data during navigation"
  - "Error categorization: Check error.response.status for specific HTTP codes, fall back to network error"

# Metrics
duration: 15min
completed: 2026-01-17
---

# Phase 14-02: UX Polish Summary

**Loading states with keepPreviousData pagination, specific error messages for auth/upload/review flows, and mobile responsive layout at 768px breakpoint**

## Performance

- **Duration:** 15 min
- **Started:** 2026-01-17T22:35:00Z
- **Completed:** 2026-01-17T22:50:00Z
- **Tasks:** 4 (3 implementation + 1 human checkpoint)
- **Files modified:** 11

## Accomplishments

- Pagination no longer flashes skeleton during page changes (keepPreviousData)
- Login page distinguishes invalid credentials from network errors
- Upload page shows specific messages for file validation failures
- Approve/reject hooks handle already-reviewed and not-found edge cases
- Sidebar collapses at 768px (tablet) instead of 1024px (laptop)
- Tables scroll horizontally on narrow screens
- CSS utilities added for touch targets and mobile-safe bottom padding

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit and fix loading states** - `910364a` (feat)
2. **Task 2: Audit and improve error messages** - `cd1a9d4` (feat)
3. **Task 3: Mobile responsiveness check and fixes** - `dff65c3` (feat)
4. **Task 4: Human verification checkpoint** - Approved by user

## Files Created/Modified

- `web/src/hooks/useAnalyses.ts` - Added keepPreviousData option
- `web/src/pages/LoginPage.tsx` - Specific credential vs network error messages
- `web/src/pages/UploadPage.tsx` - Specific upload failure messages
- `web/src/hooks/useApproveAnalysis.ts` - Handle 400/404 status codes
- `web/src/hooks/useRejectAnalysis.ts` - Handle 400/404 status codes
- `web/src/components/analysis/AuditTimeline.tsx` - Improved empty state
- `web/src/lib/file-utils.ts` - Clearer validation messages
- `web/src/components/layout/Sidebar.tsx` - Changed lg: to md: breakpoint
- `web/src/components/layout/MainLayout.tsx` - Changed lg: to md: breakpoint
- `web/src/components/layout/Header.tsx` - Mobile padding
- `web/src/components/analysis/AnalysisTable.tsx` - Horizontal scroll wrapper
- `web/src/index.css` - Touch target and mobile utilities

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| keepPreviousData | TanStack Query option that maintains stale data during refetch, eliminating skeleton flash |
| 768px breakpoint | Standard tablet width, more useful than 1024px which leaves sidebar too long on tablets |
| Error status code checks | Backend returns predictable codes (400 for already reviewed, 404 for not found) |

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- UX polish complete, ready for production deployment
- Build passes with no errors
- Human verified loading states, error messages, and mobile layout
- Phase 14-03 (deployment) can proceed

---
*Phase: 14-polish-deploy*
*Completed: 2026-01-17*
