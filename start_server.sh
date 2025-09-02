#!/bin/bash

# Install Playwright browsers if they don't exist
if [ ! -d "/root/.cache/ms-playwright" ]; then
    echo "Installing Playwright browsers..."
    playwright install chromium
    playwright install-deps
fi

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port $PORT