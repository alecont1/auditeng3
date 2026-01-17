---
phase: 08-layout-components
plan: 01
subsystem: ui
tags: [react, tailwind, shadcn-ui, layout, navigation, sidebar, breadcrumbs]

# Dependency graph
requires:
  - phase: 07-03
    provides: React Router, AuthContext, useAuth hook, ProtectedRoute
provides:
  - MainLayout app shell with sidebar + header + content area
  - Sidebar navigation with NavLink active states
  - Header with mobile hamburger menu, breadcrumbs, user dropdown
  - UserDropdown with email display and logout action
  - Breadcrumbs for path-based navigation
affects: [09-upload, 10-dashboard, 11-details, 12-reports]

# Tech tracking
tech-stack:
  added: ["@radix-ui/react-dropdown-menu", "@radix-ui/react-avatar", "@radix-ui/react-separator"]
  patterns: [layout-pattern, mobile-responsive-sidebar, breadcrumb-navigation]

key-files:
  created:
    - web/src/components/layout/MainLayout.tsx
    - web/src/components/layout/Sidebar.tsx
    - web/src/components/layout/Header.tsx
    - web/src/components/layout/UserDropdown.tsx
    - web/src/components/layout/Breadcrumbs.tsx
    - web/src/components/layout/index.ts
    - web/src/components/ui/dropdown-menu.tsx
    - web/src/components/ui/avatar.tsx
    - web/src/components/ui/separator.tsx
  modified:
    - web/src/App.tsx
    - web/src/pages/DashboardPage.tsx
    - web/package.json

key-decisions:
  - "Fixed sidebar 240px width on desktop, overlay on mobile"
  - "NavLink for active state styling on navigation items"
  - "Breadcrumbs parse pathname and map to labels"

patterns-established:
  - "Layout pattern: MainLayout wraps protected routes for consistent shell"
  - "Mobile-first responsive: sidebar hidden by default on mobile, overlay on toggle"
  - "useAuth hook for user context in UserDropdown"

# Metrics
duration: 5min
completed: 2026-01-17
---

# Phase 08 Plan 01: App Shell & Navigation Summary

**Application shell with 240px fixed sidebar, sticky header with breadcrumbs and user dropdown, mobile-responsive overlay sidebar, and NavLink navigation with active states.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-17T17:10:00Z
- **Completed:** 2026-01-17T17:15:00Z
- **Tasks:** 4
- **Files created:** 9
- **Files modified:** 3

## Accomplishments

- Added shadcn dropdown-menu, avatar, and separator components
- Created MainLayout with fixed sidebar (desktop) and overlay (mobile)
- Created Sidebar with NavLink navigation and active state styling
- Created Header with hamburger menu, breadcrumbs, and user dropdown slots
- Created UserDropdown with avatar, email display, and logout action
- Created Breadcrumbs that parse pathname and show navigation path
- Integrated MainLayout into App.tsx wrapping protected routes
- Simplified DashboardPage to content-only (layout handled by MainLayout)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add shadcn dropdown and avatar components** - `7743118` (feat)
2. **Task 2: Create MainLayout, Sidebar, and Header components** - `228fde0` (feat)
3. **Task 3: Create UserDropdown and Breadcrumbs components** - `050550b` (feat)
4. **Task 4: Integrate MainLayout into App routes** - `9945b5d` (feat)

## Files Created/Modified

- `web/src/components/layout/MainLayout.tsx` - App shell with sidebar + header + content area
- `web/src/components/layout/Sidebar.tsx` - Navigation sidebar with NavLink active states, mobile overlay
- `web/src/components/layout/Header.tsx` - Sticky header with hamburger, breadcrumbs, user dropdown
- `web/src/components/layout/UserDropdown.tsx` - User menu with email and logout via useAuth
- `web/src/components/layout/Breadcrumbs.tsx` - Path-based breadcrumb navigation
- `web/src/components/layout/index.ts` - Barrel exports for layout components
- `web/src/components/ui/dropdown-menu.tsx` - shadcn DropdownMenu component
- `web/src/components/ui/avatar.tsx` - shadcn Avatar component
- `web/src/components/ui/separator.tsx` - shadcn Separator component
- `web/src/App.tsx` - Added MainLayout wrapper for protected routes
- `web/src/pages/DashboardPage.tsx` - Simplified to content-only (no header/layout)
- `web/package.json` - Added Radix UI dependencies for dropdown, avatar, separator

## Decisions Made

1. **Fixed sidebar 240px width** - Standard SaaS app shell width, collapsible on mobile
2. **NavLink for navigation** - Uses react-router-dom NavLink for automatic active state
3. **Breadcrumbs from pathname** - Parse pathname segments and map to labels, handles IDs
4. **User dropdown with logout** - Uses useAuth hook for user email and logout action

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] shadcn components created in wrong directory**

- **Found during:** Task 1 (Adding shadcn components)
- **Issue:** shadcn CLI created files in literal `@/` directory instead of `src/`
- **Fix:** Moved files from `web/@/components/ui/` to `web/src/components/ui/` and removed empty `@/` dir
- **Files modified:** dropdown-menu.tsx, avatar.tsx, separator.tsx locations
- **Verification:** ls web/src/components/ui/ shows all expected components
- **Committed in:** 7743118 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope creep, just path correction for shadcn output (same issue as 07-03).

## Issues Encountered

None - all tasks completed successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 08-01 (App Shell & Navigation) complete
- Layout structure ready for all protected pages
- Ready for 08-02-PLAN.md (Common Components)

---
*Phase: 08-layout-components*
*Completed: 2026-01-17*
