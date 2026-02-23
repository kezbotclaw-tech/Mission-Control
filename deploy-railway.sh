#!/bin/bash
# Deploy Mission Control to Railway

echo "🚀 Deploying Mission Control to Railway..."
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login with token
export RAILWAY_TOKEN=ac005728-192a-4235-9c7a-dbb89bcea7d4

# Link to project (or create new one)
echo "Creating Railway project..."
railway init --name "mission-control"

# Add environment variables
echo "Setting environment variables..."
railway variables set SECRET_KEY="$(openssl rand -hex 32)"
railway variables set PORT="8080"

# Deploy
echo "Deploying..."
railway up

echo ""
echo "✅ Deployment complete!"
echo "🔗 Your app will be available at: https://mission-control.up.railway.app"
echo ""
echo "To check status: railway status"
echo "To view logs: railway logs"
