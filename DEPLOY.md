# Mission Control - Railway Deployment Guide

This guide will walk you through deploying Mission Control to Railway.

## Prerequisites

- A [Railway](https://railway.app) account
- Your code pushed to a GitHub repository
- Git installed locally

## Quick Deploy

### Option 1: One-Click Deploy (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click the button above or go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your Mission Control repository
4. Railway will automatically detect the configuration from `railway.toml`

### Option 2: Manual Deploy

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. In Railway Dashboard:
   - Click "New Project"
   - Select "GitHub Repo"
   - Choose your repository
   - Click "Deploy"

## Environment Variables

Set these in Railway Dashboard → Your Project → Variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **Yes** | Flask secret key (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | Auto | Railway PostgreSQL URL (auto-added when you provision PostgreSQL) |
| `PORT` | Auto | Port to run on (Railway sets this automatically) |

### Generate a Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and set it as `SECRET_KEY` in Railway variables.

## Adding a Database

Mission Control works with both SQLite and PostgreSQL. For production, use PostgreSQL:

1. In Railway Dashboard, click "New" → "Database" → "Add PostgreSQL"
2. Railway will automatically set `DATABASE_URL`
3. Redeploy if needed

## Deployment Files Explained

| File | Purpose |
|------|---------|
| `railway.toml` | Railway configuration (build settings, health checks, deploy settings) |
| `requirements.txt` | Python dependencies |
| `Procfile` | Process definition for web server |
| `Dockerfile` | Container configuration (optional, Railway can use Nixpacks instead) |
| `app_railway.py` | Production-ready Flask application |
| `.env.example` | Template for environment variables |

## Post-Deployment

### Verify Deployment

1. Check the deployment logs in Railway Dashboard
2. Once deployed, Railway will provide a URL like `https://your-app.up.railway.app`
3. Visit the `/health` endpoint to verify: `https://your-app.up.railway.app/health`

You should see:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-23T20:00:00"
}
```

### Troubleshooting

**App won't start:**
- Check logs in Railway Dashboard
- Verify `SECRET_KEY` is set
- Check that `PORT` environment variable is being used

**Database connection errors:**
- If using PostgreSQL: Ensure `DATABASE_URL` is set correctly
- If using SQLite: Ensure the `/app/data` directory exists (Dockerfile creates this)

**Static files not loading:**
- Verify `static_folder='static'` in app_railway.py
- Check that static files are in the `static/` directory

## Local Development

Run locally before deploying:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and set SECRET_KEY

# Run the app
python app_railway.py
```

Visit http://localhost:5000

## Custom Domain (Optional)

1. In Railway Dashboard → Your Project → Settings
2. Click "Custom Domain"
3. Add your domain and follow the DNS instructions

## Monitoring

- **Logs**: Railway Dashboard → Your Project → Deployments → Logs
- **Metrics**: Railway Dashboard → Your Project → Metrics
- **Health**: Visit `/health` endpoint

## Updates

To update your deployed app:

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. Railway will automatically redeploy

## Support

- Railway Docs: https://docs.railway.app
- Flask Docs: https://flask.palletsprojects.com
- PostgreSQL Docs: https://www.postgresql.org/docs/

## Security Notes

- Always use a strong `SECRET_KEY` in production
- Never commit `.env` files with real credentials
- Enable HTTPS (Railway provides this automatically)
- Regularly update dependencies: `pip list --outdated`
