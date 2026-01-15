# Testing

*Last updated: 2026-01-15*

## Current Status

**No active test implementations** - Test frameworks are installed but no tests have been written yet.

## Test Frameworks

### TypeScript
- **Node.js Test Runner** - Native testing via `tsx --test`
- **Playwright 1.57.0** - E2E testing capability (`auditeng/lop-agx/package.json`)
- No test files currently present (*.test.ts, *.spec.ts)

### Python
- **pytest** - Test framework (`audit/audit/pyproject.toml`)
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- Test structure exists but empty (`audit/audit/tests/`)

## Test Organization

### TypeScript (Planned)
```
apps/api/src/
├── modules/
│   ├── auth/
│   │   ├── auth.routes.ts
│   │   └── auth.routes.test.ts    # Co-located tests
│   └── analysis/
│       ├── analysis.service.ts
│       └── analysis.service.test.ts
└── __tests__/                      # Integration tests
    └── api.integration.test.ts

e2e/                                # Playwright E2E tests
└── flows/
    └── login.spec.ts
```

### Python
```
audit/audit/tests/
├── conftest.py                    # Fixtures defined
├── unit/
│   ├── __init__.py
│   └── core/
│       └── __init__.py
├── integration/
│   └── __init__.py
└── fixtures/
    ├── __init__.py
    └── reports/                   # Test PDF files (empty)
```

## Available Fixtures (Python)

From `audit/audit/tests/conftest.py`:
- `test_user` - Creates test user with credentials
- `auth_token` - JWT access token for authenticated requests
- `client` - TestClient for API testing
- Requires PostgreSQL on localhost:5432

## Code Quality Tools

### Linting
- **ESLint** - TypeScript linting (`pnpm lint`)
- No custom `.eslintrc` - uses defaults

### Type Checking
- **TypeScript** - Strict mode enabled
- `pnpm typecheck` - Type validation

### TypeScript Compiler Options
```json
{
  "strict": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noImplicitReturns": true,
  "noFallthroughCasesInSwitch": true
}
```

## Coverage

### Configuration (Python)
From `audit/audit/pyproject.toml`:
```toml
[tool.coverage.run]
source = ["app"]
branch = true

[tool.coverage.report]
fail_under = 85  # Will fail - no tests exist
```

### TypeScript
- No coverage configuration
- `coverage/` directory in `.gitignore`

## Development Scripts

### TypeScript Monorepo
```bash
pnpm test          # Run tests recursively (no tests yet)
pnpm lint          # ESLint on all packages
pnpm typecheck     # TypeScript validation
```

### Python
```bash
pytest             # Run tests
pytest --cov=app   # With coverage
```

## E2E Testing

### Playwright Setup
- Configuration: `auditeng/lop-agx/.playwright-mcp/`
- Installed: `@playwright/test@^1.57.0`
- No test files written yet

### Suggested E2E Tests
- Login flow
- Analysis upload and processing
- Dashboard interactions
- Settings management

## Recommendations

1. **Write unit tests** for service layer functions
2. **Add integration tests** for API endpoints
3. **Create E2E tests** for critical user flows
4. **Add test coverage reporting** to CI/CD
5. **Create test fixtures** with sample PDF reports
6. **Mock external services** (Claude API, Stripe)
