"""
CrimeVision AI - Intelligent Multimodal Forensic Analysis Platform
Main FastAPI application entry point.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path so direct execution works from any directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import HOST, PORT, FRONTEND_DIR, UPLOAD_DIR, REPORTS_DIR
from backend.api.routes import router as api_router

# Ensure runtime directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="CrimeVision AI",
    description="Intelligent Multimodal Forensic Analysis Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for local development & cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST API routes
app.include_router(api_router)

# Mount frontend static directories if they exist
css_dir = FRONTEND_DIR / "css"
js_dir = FRONTEND_DIR / "js"
assets_dir = FRONTEND_DIR / "assets"

if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
async def serve_index():
    """Serve the primary CrimeVision AI frontend dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "CrimeVision AI API",
        "status": "online",
        "docs": "/docs",
        "frontend": "Frontend template is being prepared"
    }


if __name__ == "__main__":
    print(f"🚀 Starting CrimeVision AI on http://{HOST}:{PORT}")
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
