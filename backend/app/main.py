"""
Topo-Opt-Web Backend — FastAPI Application (Phase 2)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api import geometry, optimization, health

app = FastAPI(
    title="Topo-Opt-Web API",
    description="Topologie-Optimierung Backend mit 3D-Geometrieverarbeitung, CAD-Style BCs, und Named Selections",
    version="0.3.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(geometry.router, prefix="/api/geometry", tags=["geometry"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["optimization"])

# Serve uploaded/result files
UPLOAD_DIR = Path("uploads")
RESULT_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup():
    print("🏗️  Topo-Opt-Web Backend v0.3.0 gestartet")
    print("📐 STEP-Support:", "verfügbar" if _check_occ() else "nicht verfügbar (pythonocc fehlt)")


def _check_occ() -> bool:
    try:
        from OCP.STEPControl import STEPControl_Reader
        return True
    except ImportError:
        return False
