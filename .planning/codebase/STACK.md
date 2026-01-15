# Technology Stack

*Last updated: 2026-01-15*

## Languages

**Primary:**
- TypeScript 5.4.5 - All application code (`auditeng/lop-agx/apps/web/package.json`, `auditeng/lop-agx/apps/api/package.json`)
- Python 3.11+ - Backend AI processing (`audit/audit/pyproject.toml`)

**Secondary:**
- JavaScript - Build configs (`auditeng/lop-agx/apps/web/tailwind.config.js`, `postcss.config.js`)

## Runtime Environment

- **Node.js >=18.0.0** - Backend runtime (`auditeng/lop-agx/package.json` engines field)
- **Python 3.11+** - FastAPI backend (`audit/audit/docker/Dockerfile`)
- **Browser/Web** - Frontend runtime with React

## Package Manager

- **pnpm 9.0.0** - TypeScript monorepo (`auditeng/lop-agx/package.json` packageManager field)
- **pip** - Python dependencies (`audit/audit/pyproject.toml`)
- **pnpm-lock.yaml** - Dependency lockfile

## Frameworks

### Frontend (Web)
- **React 18.3.1** - UI framework (`auditeng/lop-agx/apps/web/package.json`)
- **Vite 5.3.1+** - Build tool and dev server (`auditeng/lop-agx/apps/web/vite.config.ts`)
- **React Router DOM 6.23.1** - Client-side routing
- **Tailwind CSS 3.4.4** - Utility-first CSS (`auditeng/lop-agx/apps/web/tailwind.config.js`)
- **Radix UI** - Accessible UI components

### Backend (TypeScript API)
- **Hono 4.4.0+** - Lightweight web framework (`auditeng/lop-agx/apps/api/src/index.ts`)
- **@hono/node-server 1.12.0+** - Node.js server adapter
- **Prisma 5.15.0** - ORM for PostgreSQL (`auditeng/lop-agx/apps/api/src/lib/prisma.ts`)

### Backend (Python API)
- **FastAPI** - Async web framework (`audit/audit/app/main.py`)
- **SQLAlchemy 2.0** - Async ORM (`audit/audit/app/db/session.py`)
- **Alembic** - Database migrations (`audit/audit/alembic/`)
- **Pydantic v2** - Data validation (`audit/audit/app/schemas/`)

## Key Dependencies

### Core Libraries (TypeScript)
- **Zod 3.23.8+** - Runtime type validation (`auditeng/lop-agx/apps/api/src/modules/analysis/analysis.routes.ts`)
- **jose 5.4.0+** - JWT handling (`auditeng/lop-agx/apps/api/src/lib/jwt.ts`)
- **bcryptjs 3.0.3** - Password hashing (`auditeng/lop-agx/apps/api/src/lib/password.ts`)
- **dotenv 17.2.3** - Environment variables

### Core Libraries (Python)
- **instructor** - Structured AI extraction
- **python-jose** - JWT authentication
- **bcrypt** - Password hashing
- **aiosqlite/asyncpg** - Async database drivers

### UI Components
- **@radix-ui/react-*** - Accessible component library
- **class-variance-authority 0.7.0** - Component variants
- **clsx 2.1.1** - Conditional CSS classes
- **tailwind-merge 2.3.0** - Tailwind class merging
- **lucide-react 0.395.0** - Icon library

### File Processing
- **pdf2pic 3.2.0** - PDF to image conversion (`auditeng/lop-agx/apps/api/package.json`)
- **pdf-to-img 5.0.0** - PDF image extraction
- **sharp 0.34.5** - Image processing
- **react-dropzone 14.2.3+** - File upload component

### Cloud & Infrastructure
- **@aws-sdk/client-s3 3.600.0** - AWS S3 / Cloudflare R2 storage
- **ioredis 5.4.1+** - Redis client for rate limiting

## Configuration

### Environment Files
- Root config: `auditeng/lop-agx/.env.example`
- API config: `auditeng/lop-agx/apps/api/.env.example`
- Web config: `auditeng/lop-agx/apps/web/.env`
- Python API: `audit/audit/app/.env.example`

### TypeScript Config
- `auditeng/lop-agx/apps/web/tsconfig.json` - Strict mode enabled
- `auditeng/lop-agx/apps/api/tsconfig.json` - Strict mode enabled

### Build Config
- `auditeng/lop-agx/apps/web/vite.config.ts` - Vite with API proxy
- `auditeng/lop-agx/apps/web/tailwind.config.js` - Tailwind theme
- `auditeng/lop-agx/apps/web/postcss.config.js` - PostCSS plugins

### Database
- `auditeng/lop-agx/apps/api/prisma/schema.prisma` - PostgreSQL schema
- `audit/audit/alembic.ini` - SQLAlchemy migrations config
