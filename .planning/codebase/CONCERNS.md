# Technical Concerns

*Last updated: 2026-01-15*

## Critical Issues

### 1. Feature Blocker: No Redis Queue Integration
- **Location**: `audit/audit/app/api/v1/analyze.py:101`
- **Issue**: TODO comment - tasks are created with QUEUED status but never processed
- **Impact**: Core analysis feature does not work
- **Fix**: Implement Redis/RQ job queue integration

### 2. CORS Allows All Origins
- **Location**: `audit/audit/app/main.py:37`
- **Issue**: `allow_origins=["*"]` with credentials enabled
- **Impact**: Security vulnerability in production
- **Fix**: Configure allowed origins via environment variable

## Security Concerns

### Hardcoded Default Secret Key
- **Location**: `audit/audit/app/config.py:34`
- **Issue**: Defaults to `"dev-secret-key-change-in-production"`
- **Risk**: Accidental deployment with insecure default
- **Fix**: Require explicit secret in production

### File Upload Error Handling
- **Location**: `audit/audit/app/api/v1/analyze.py:85-86`
- **Issue**: No try-catch around file I/O operations
- **Risk**: Unhandled OSError, IOError, PermissionError
- **Fix**: Add exception handling for disk operations

### No Token Blacklisting
- **Location**: `audit/audit/app/api/v1/auth.py:108`
- **Issue**: Logout doesn't invalidate tokens
- **Risk**: Tokens valid until expiration after logout
- **Fix**: Implement token blacklist in Redis

## Missing Features

### Empty Core Modules (Python)
- `audit/audit/app/core/agents/` - No AI extraction logic
- `audit/audit/app/core/validators/` - No validation rules
- `audit/audit/app/core/rules/` - No NETA/Microsoft standards
- `audit/audit/app/services/` - No external integrations
- `audit/audit/app/worker/` - No background job definitions

### No Database Migrations
- **Location**: `audit/audit/alembic/versions/` - Empty
- **Issue**: Uses `create_all()` instead of versioned migrations
- **Risk**: No schema evolution path for production
- **Fix**: Create initial migration before first deploy

## Testing Gaps

### No Test Implementations
- `audit/audit/tests/unit/` - Only `__init__.py` files
- `audit/audit/tests/integration/` - Empty
- `audit/audit/tests/fixtures/reports/` - No test data
- **Coverage**: Configured to fail under 85% (will fail)

### TypeScript Tests Missing
- No `*.test.ts` or `*.spec.ts` files found
- Playwright installed but unused
- Test command exists but nothing to run

## Performance Concerns

### In-Memory File Loading
- **Location**: `audit/audit/app/api/v1/analyze.py:62`
- **Issue**: `await file.read()` loads entire file before size check
- **Impact**: Memory pressure for large PDFs (up to 50MB)
- **Fix**: Stream and check size incrementally

### N+1 Query Pattern
- **Location**: `audit/audit/app/db/repositories/tasks.py:103`
- **Issue**: `update()` calls `get_by_id()` then updates
- **Impact**: Extra database round-trip
- **Fix**: Use direct UPDATE statement

## Documentation Gaps

### Validation Rules Not Implemented
- **Location**: README.md documents 32+ rules but `app/core/` is empty
- **Issue**: Documentation promises features that don't exist
- **Fix**: Implement validators or update documentation

### Complex Code Undocumented
- **Location**: `audit/audit/app/db/models.py:15-29`
- **Issue**: `JSONType` class lacks explanation
- **Purpose**: PostgreSQL vs SQLite compatibility
- **Fix**: Add docstrings explaining the pattern

## Dependency Concerns

### Flexible Version Constraints
- **Location**: `audit/audit/pyproject.toml`
- **Issue**: Uses `>=` constraints (e.g., `fastapi>=0.109.0`)
- **Risk**: Breaking changes from dependency updates
- **Fix**: Pin versions or use lock file

### No Lock File
- Missing `poetry.lock` or `requirements.lock`
- Risk: Non-reproducible builds
- Fix: Generate and commit lock file

## Architecture Concerns

### Incomplete Repository Pattern
- Only `TaskRepository` and `UserRepository` exist
- Other models would need repositories
- Consider service layer for complex business logic

### No Logging
- Zero logging statements in application code
- Production debugging will be difficult
- Add structured logging with levels

## Database Concerns

### SQLite Default vs PostgreSQL Production
- **Location**: `audit/audit/app/config.py:24`
- **Issue**: Defaults to SQLite but docs assume PostgreSQL
- **Risk**: Local/production behavior differences
- **Fix**: Require explicit database URL configuration

## Summary Table

| Category | Issue | Location | Severity |
|----------|-------|----------|----------|
| Feature | No queue integration | `analyze.py:101` | **CRITICAL** |
| Security | CORS wildcard | `main.py:37` | **HIGH** |
| Security | File I/O unhandled | `analyze.py:85-86` | **HIGH** |
| Testing | No tests | `tests/` | **HIGH** |
| Documentation | Rules not implemented | `core/` vs README | **MEDIUM** |
| Database | No migrations | `alembic/versions/` | **MEDIUM** |
| Performance | Memory loading | `analyze.py:62` | **LOW** |
| Architecture | Empty modules | `core/`, `services/` | **MEDIUM** |

## Priority Recommendations

1. Implement Redis queue integration (blocking)
2. Add try-catch for file operations (security)
3. Restrict CORS origins (security)
4. Write tests (quality)
5. Implement validators and rules (features)
6. Add logging (operations)
7. Pin dependency versions (stability)
8. Add database migrations (production-readiness)
