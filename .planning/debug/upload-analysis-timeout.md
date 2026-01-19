---
status: verifying
trigger: "upload-analysis-timeout: PDF report uploads start but fail with ERR_CONNECTION_TIMED_OUT on /api/auth/me endpoint"
created: 2026-01-19T00:00:00Z
updated: 2026-01-19T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - Frontend was built with wrong/stale VITE_API_URL pointing to non-existent Railway service
test: Check built JS bundle for actual API URL
expecting: Find a mismatch between expected and actual URL
next_action: Rebuild frontend with correct VITE_API_URL=backend-api-production-c20f.up.railway.app

## Symptoms

expected: When user uploads PDF reports for analysis, the upload should complete and analysis should run successfully
actual: Upload starts, loads for a while, then fails with connection timeout. Console shows ERR_CONNECTION_TIMED_OUT on /api/auth/me, TypeError about 'redirectTo'
errors:
- net::ERR_CONNECTION_TIMED_OUT on /api/auth/me
- TypeError: Cannot read properties of undefined (reading 'redirectTo')
reproduction: Upload any PDF file
started: Never worked in production

## Eliminated

- hypothesis: Backend /api/auth/me endpoint is slow or missing
  evidence: curl https://backend-api-production-c20f.up.railway.app/api/auth/me returns 401 "Not authenticated" immediately (< 1 second)
  timestamp: 2026-01-19

- hypothesis: CORS is blocking the request
  evidence: CORS preflight returns 200 with correct Access-Control-Allow-Origin header for Railway origins
  timestamp: 2026-01-19

- hypothesis: Backend API routing is misconfigured
  evidence: All API endpoints work correctly via curl
  timestamp: 2026-01-19

## Evidence

- timestamp: 2026-01-19
  checked: Built frontend JavaScript bundle
  found: VITE_API_URL baked into build is "worker-production-a0a1.up.railway.app"
  implication: Frontend is calling wrong API URL

- timestamp: 2026-01-19
  checked: Production backend health endpoint
  found: https://backend-api-production-c20f.up.railway.app/api/health returns 200 OK
  implication: Correct backend URL works fine

- timestamp: 2026-01-19
  checked: Old backend URL in built bundle
  found: https://worker-production-a0a1.up.railway.app/api/health returns 404 "Application not found"
  implication: Old Railway service was deleted/renamed, frontend still pointing to it

- timestamp: 2026-01-19
  checked: Backend /api/auth/me with correct URL
  found: Returns 401 "Not authenticated" as expected
  implication: Backend endpoint works, issue is URL mismatch

## Resolution

root_cause: Frontend was built with stale VITE_API_URL environment variable pointing to "worker-production-a0a1.up.railway.app" which no longer exists (returns 404 "Application not found"). The correct backend URL is "backend-api-production-c20f.up.railway.app". This causes ERR_CONNECTION_TIMED_OUT as the browser cannot connect to the non-existent service.

fix:
1. Updated web/.env.example with clearer documentation about VITE_API_URL
2. Rebuilt frontend with VITE_API_URL=backend-api-production-c20f.up.railway.app
3. Verified new build contains correct URL in bundle

RAILWAY DEPLOYMENT FIX REQUIRED:
In Railway dashboard, update the "web" service environment variables:
  VITE_API_URL=backend-api-production-c20f.up.railway.app
Then redeploy the frontend service.

verification:
- Local build verified: grep shows "backend-api-production-c20f.up.railway.app" in JS bundle
- Backend endpoint verified: curl returns proper responses
- Needs deployment to Railway to verify in production

files_changed:
- web/.env.example (documentation improvement)
- web/dist/* (rebuilt with correct URL)
