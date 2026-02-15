"""TopoOpt Web - Backend API"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import geometry, optimization, health
from app.core.config import settings

app = FastAPI(
    title="TopoOpt Web API",
    description="Topology Optimization Web Application API",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(geometry.router, prefix="/api/geometry", tags=["Geometry"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["Optimization"])


@app.on_event("startup")
async def startup():
    logger.info("TopoOpt Web API starting up...")
    logger.info(f"Upload dir: {settings.UPLOAD_DIR}")
    logger.info(f"Results dir: {settings.RESULTS_DIR}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("TopoOpt Web API shutting down...")
