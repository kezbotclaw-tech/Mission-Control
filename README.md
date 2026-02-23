# Mission Control - Railway Deployment Package

This folder contains everything needed to deploy Mission Control to Railway.

## Files Included

| File | Description |
|------|-------------|
| `railway.toml` | Railway configuration with build settings, health checks, and deployment settings |
| `requirements.txt` | Python dependencies (Flask, Gunicorn, PostgreSQL adapter) |
| `Procfile` | Process definition for the web server |
| `Dockerfile` | Multi-stage container build for production deployment |
| `app_railway.py` | Production-ready Flask application with PostgreSQL/SQLite support |
| `.env.example` | Environment variables template |
| `DEPLOY.md` | Step-by-step deployment guide |
| `templates/` | HTML templates (copied from web-app-v2) |
| `static/` | CSS and JavaScript files |

## Key Features

### Production-Ready App (`app_railway.py`)

- ✅ Uses Railway's `PORT` environment variable
- ✅ Supports Railway's `DATABASE_URL` for PostgreSQL
- ✅ Falls back to SQLite for local development
- ✅ Proper logging for production
- ✅ Health check endpoint at `/health`
- ✅ Security settings (no debug mode, proper secret key handling)
- ✅ Error handlers for 404 and 500 errors
- ✅ Database abstraction layer supporting both SQLite and PostgreSQL

### Health Check

The `/health` endpoint returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-23T20:00:00"
}
```

### Database Support

- **PostgreSQL**: Used automatically when `DATABASE_URL` is set (Railway provides this)
- **SQLite**: Fallback for local development when `DATABASE_URL` is not set

## Quick Start

1. Copy these files to your repository root (or use this folder)
2. Set environment variables in Railway Dashboard:
   - `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
3. Add PostgreSQL database in Railway (optional but recommended)
4. Deploy!

See `DEPLOY.md` for detailed instructions.

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
cp .env.example .env
# Edit .env and add your SECRET_KEY

# Run
python app_railway.py
```

Visit http://localhost:5000

## Deployment Checklist

- [ ] `SECRET_KEY` environment variable set in Railway
- [ ] PostgreSQL database provisioned (recommended)
- [ ] Templates copied to `templates/` folder
- [ ] Static files in `static/` folder
- [ ] `/health` endpoint responds with 200 OK
- [ ] Dashboard loads at root URL `/`
