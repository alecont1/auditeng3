# External Integrations

*Last updated: 2026-01-15*

## AI Services

### Anthropic Claude API
- **SDK**: `@anthropic-ai/sdk 0.25.2` (`auditeng/lop-agx/apps/api/package.json`)
- **Implementation**: `auditeng/lop-agx/apps/api/src/modules/ai/extractors/claude-extractor.ts`
- **Model**: `claude-sonnet-4-20250514`
- **Environment**: `ANTHROPIC_API_KEY`

**Capabilities:**
- Thermal image analysis
- Visible photo extraction
- Calibration certificate reading
- Structured data extraction

## Payment Processing

### Stripe
- **SDK**: `stripe 15.8.0+` (`auditeng/lop-agx/apps/api/package.json`)
- **Implementation**:
  - `auditeng/lop-agx/apps/api/src/lib/stripe.ts`
  - `auditeng/lop-agx/apps/api/src/modules/tokens/tokens.routes.ts`
- **API Version**: 2024-04-10

**Environment Variables:**
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PUBLISHABLE_KEY`

**Token Packages:**
| Package | Tokens | Purpose |
|---------|--------|---------|
| Starter | 50,000 | Entry tier |
| Basic | 150,000 | Small teams |
| Professional | 400,000 | Medium usage |
| Business | 1,000,000 | High volume |
| Enterprise | 3,000,000 | Large scale |

**Webhook Events:**
- `checkout.session.completed`

## Database

### PostgreSQL
- **ORM (TypeScript)**: Prisma 5.15.0+
- **ORM (Python)**: SQLAlchemy 2.0 async
- **Schema**: `auditeng/lop-agx/apps/api/prisma/schema.prisma`
- **Environment**: `DATABASE_URL`

**Models (Prisma):**
- Company
- User
- Invitation
- Analysis
- TokenTransaction
- AuditLog

**Models (SQLAlchemy):**
- User
- Task

## Cloud Storage

### Cloudflare R2 (AWS S3 Compatible)
- **SDK**: `@aws-sdk/client-s3 3.600.0`
- **Status**: Configured but optional
- **Purpose**: PDF file storage

**Environment Variables:**
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_PUBLIC_URL`

## Caching & Session

### Redis
- **SDK**: `ioredis 5.4.1+`
- **Usage**: `auditeng/lop-agx/apps/api/src/lib/rate-limiter.ts`
- **Environment**: `REDIS_URL`

**Current Implementation:**
- In-memory rate limiting (development)
- Comment suggests Redis for distributed environments

## Authentication

### JWT (JSON Web Tokens)
- **Library (TypeScript)**: `jose` (`auditeng/lop-agx/apps/api/src/lib/jwt.ts`)
- **Library (Python)**: `python-jose`
- **Algorithm**: HS256
- **Token Expiry**: 7 days
- **Environment**: `JWT_SECRET`

### Password Hashing
- **Library (TypeScript)**: `bcryptjs` (`auditeng/lop-agx/apps/api/src/lib/password.ts`)
- **Library (Python)**: `bcrypt`
- **Salt Rounds**: 10
- **Validation**: Min 8 chars, 1 letter, 1 number

## PDF Processing

### PDF to Image Pipeline
- **pdf2pic 3.2.0** - PDF to image conversion
- **pdf-to-img 5.0.0** - PDF image extraction
- **sharp 0.34.5** - Image optimization

**Implementation**: `auditeng/lop-agx/apps/api/src/modules/analysis/analysis.service.ts`

## Rate Limiting

- **Implementation**: `auditeng/lop-agx/apps/api/src/lib/rate-limiter.ts`
- **Configuration**: 10 requests/minute per IP (analysis endpoints)
- **Note**: Production should use Redis for distributed rate limiting

## Audit Logging

- **Implementation**: `auditeng/lop-agx/apps/api/src/lib/audit-log.ts`
- **IP Tracking**: Captured from request headers

**Tracked Actions:**
- LOGIN, LOGOUT, LOGIN_FAILED
- ANALYSIS_CREATED, ANALYSIS_DELETED, ANALYSIS_REANALYZED
- PROFILE_UPDATED, PASSWORD_CHANGED
- USER_INVITED, USER_DELETED
- COMPANY_CREATED, COMPANY_DELETED

## Application URLs

- **API_URL**: Backend API endpoint
- **WEB_URL**: Frontend application URL (CORS)
- **Development Proxy**: Vite proxies `/api` to port 3001

Configuration: `auditeng/lop-agx/.env.example`

## Not Detected

- Email/SMTP integration
- SMS service
- Analytics platforms
- Monitoring/APM tools
