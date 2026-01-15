# Coding Conventions

*Last updated: 2026-01-15*

## Code Style

### Indentation & Formatting
- 2-space indentation throughout TypeScript codebase
- 4-space indentation in Python
- No explicit Prettier config; uses editor defaults
- ES2020+ standards with strict TypeScript

### Semicolons & Quotes
- Semicolons used consistently in TypeScript
- Single quotes for strings in JavaScript/TypeScript
- Double quotes for strings in Python

### Import Style
- File extensions included for ES modules (`.js`, `.ts`)
- Grouped imports: external → internal → relative

Example from `auditeng/lop-agx/apps/api/src/index.ts`:
```typescript
import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
```

## Naming Conventions

### Files
- **React components**: `PascalCase.tsx` (`InviteUserModal.tsx`, `DashboardPage.tsx`)
- **Routes/services**: `kebab-case.ts` (`auth.routes.ts`, `auth.service.ts`)
- **Utilities**: `camelCase.ts` (`api.ts`, `utils.ts`)
- **Python modules**: `snake_case.py` (`base.py`, `extraction.py`)

### Variables & Functions
- camelCase for functions and variables in TypeScript
- snake_case for functions and variables in Python
- Example: `fetchTokenBalance()`, `handleSubmit()`, `get_current_user()`

### Types & Interfaces
- PascalCase for interfaces: `TokenPayload`, `AuthContextType`
- Props interfaces: `InviteUserModalProps`, `ProtectedRouteProps`
- Enum values: UPPER_SNAKE_CASE (`SUPER_ADMIN`, `APPROVED`)

### API Routes
- HTTP method + descriptive action pattern
- Example: `POST /api/auth/login`, `GET /api/analysis/:id`

## Patterns

### Module Structure (TypeScript)
Each feature module contains:
- `.routes.ts` - HTTP endpoints
- `.service.ts` - Business logic
- `.middleware.ts` - Module-specific middleware

Location: `auditeng/lop-agx/apps/api/src/modules/`

### Middleware Pattern
```typescript
// auditeng/lop-agx/apps/api/src/modules/auth/auth.middleware.ts
export const requireAuth = async (c: Context, next: Next) => {
  // Authentication logic
};
```

### Service Layer Pattern
```typescript
// Business logic in service files
export async function getUsersByCompanyId(companyId: string) {
  return prisma.user.findMany({ where: { companyId } });
}
```

### Validation Pattern
- Zod schemas for request validation
- Schema naming: `{entity}Schema` (e.g., `loginSchema`)
- Uses `safeParse()` for non-throwing validation

Example from `auditeng/lop-agx/apps/api/src/modules/auth/auth.routes.ts`:
```typescript
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const validation = loginSchema.safeParse(body);
if (!validation.success) {
  return c.json({ error: 'Validation Error', message: '...' }, 400);
}
```

### Error Response Pattern
Consistent format across all endpoints:
```typescript
return c.json({ error: 'ErrorType', message: 'description' }, statusCode);
```

### Repository Pattern (Python)
```python
# audit/audit/app/db/repositories/tasks.py
class TaskRepository:
    async def get_by_user_paginated(self, user_id: str, page: int, limit: int):
        # Type-safe async queries
```

## Documentation Style

### Inline Comments
- Limited but clear comments
- Used for explaining non-obvious logic

Example from `auditeng/lop-agx/apps/api/src/modules/auth/auth.middleware.ts`:
```typescript
// Extend Hono's context to include the user
// Middleware to require authentication
// Attach user to context
```

### TODO Comments
- Used for incomplete features
- Format: `// TODO: description`
- Examples: `// TODO: Fetch user data with token`

### Docstrings (Python)
```python
"""Brief description of module/function."""
```

## React Patterns

### Component Structure
```typescript
interface ComponentProps {
  // Props definition
}

export function Component({ prop1, prop2 }: ComponentProps) {
  // State hooks
  const [state, setState] = useState();

  // Event handlers
  const handleSubmit = async () => {};

  // Return JSX
  return <div>...</div>;
}
```

### State Management
- TanStack Query for server state
- React Context for auth state
- useState for local component state

### Protected Routes
```typescript
// auditeng/lop-agx/apps/web/src/components/ProtectedRoute.tsx
export function ProtectedRoute({ children, allowedRoles }) {
  // Role-based access control
}
```

## TypeScript Configuration

Both projects use strict mode:
```json
{
  "strict": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noImplicitReturns": true,
  "noFallthroughCasesInSwitch": true
}
```

## Python Configuration

- Type hints throughout
- Pydantic v2 for validation
- Async/await for all database operations
- SQLAlchemy 2.0 style
