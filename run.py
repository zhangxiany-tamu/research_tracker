#!/usr/bin/env python3
"""
Research Tracker - Web application to track recent papers from statistics journals
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting Research Tracker...")
    print("Web interface will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )