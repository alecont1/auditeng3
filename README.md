# AuditEng

AI-powered electrical engineering audit analysis system.

## Installation

```bash
pip install -e .
```

## Development

```bash
pip install -e ".[dev]"
```

## Railway Deployment

This project uses separate config files for web and worker services.

### Services Architecture

| Service | Config File | Start Command |
|---------|-------------|---------------|
| **web** | `railway-web.json` | `alembic upgrade head && uvicorn app.main:app` |
| **worker** | `railway-worker.json` | `dramatiq app.worker.tasks --processes 1 --threads 4` |

### Setup New Environment

1. **Create services** from GitHub repo `alecont1/auditeng3`

2. **Configure each service:**
   - Go to Service → Settings → Config-as-code
   - Select the appropriate config file:
     - Web service: `railway-web.json`
     - Worker service: `railway-worker.json`

3. **Required environment variables** (both services):
   - `DATABASE_URL` - PostgreSQL connection string
   - `REDIS_URL` - Redis connection string
   - `ANTHROPIC_API_KEY` - Claude API key
   - `JWT_SECRET_KEY` - JWT signing key
   - `FRONTEND_URL` - Frontend URL for CORS

4. **Deploy** - Railway will auto-deploy on push

### Notes

- Only the **web** service runs migrations (`alembic upgrade head`)
- The **worker** processes background tasks via Dramatiq
- Both services share the same database and Redis instances
