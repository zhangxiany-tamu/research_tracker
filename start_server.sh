#!/bin/bash

echo "🚀 Starting Research Tracker with Playwright support..."

# Install Playwright browsers if they don't exist
echo "🔧 Checking Playwright installation..."
if [ ! -d "/opt/render/project/.cache/ms-playwright" ] && [ ! -d "/root/.cache/ms-playwright" ]; then
    echo "📦 Installing Playwright browsers..."
    export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright
    python3 -m playwright install chromium --with-deps
    echo "✅ Playwright browsers installed"
else
    echo "✅ Playwright browsers already available"
fi

# Export browser path for runtime
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright

echo "🌐 Starting FastAPI server..."
# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port $PORT