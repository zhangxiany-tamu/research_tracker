#!/usr/bin/env python3
"""
Google App Engine entry point for Research Tracker
"""
import os
from app.main import app as fastapi_app
from app.database import create_tables

# Initialize database on startup
create_tables()

# Expose the app for uvicorn
app = fastapi_app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)