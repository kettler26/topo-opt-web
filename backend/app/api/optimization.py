"""Optimization endpoints."""
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.config import settings
from app.models.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationStatus,
)
from app.solver.simp import SIMPSolver

router = APIRouter()

# In-memory job store (replace with DB in production)
jobs: dict[str, dict] = {}


@router.post("/run", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    """Start a topology optimization job."""
    job_id = str(uuid.uuid4())

    # Verify geometry exists
    upload_dir = Path(settings.UPLOAD_DIR)
    geometry_file = None
    for f in upload_dir.iterdir():
        if f.stem == request.geometry_id:
            geometry_file = f
            break

    if geometry_file is None:
        raise HTTPException(status_code=404, detail="Geometry not found")

    # Create job
    jobs[job_id] = {
        "id": job_id,
        "status": "running",
        "geometry_id": request.geometry_id,
        "parameters": request.model_dump(),
        "progress": 0.0,
        "result": None,
    }

    logger.info(f"Starting optimization job {job_id} for geometry {request.geometry_id}")

    try:
        solver = SIMPSolver(
            volume_fraction=request.volume_fraction,
            penalty=request.penalty,
            filter_radius=request.filter_radius,
            max_iterations=request.max_iterations,
        )

        # Run solver (synchronous for MVP, async job queue in Phase 3)
        result = solver.optimize(
            geometry_path=str(geometry_file),
            boundary_conditions=request.boundary_conditions,
        )

        # Save result
        results_dir = Path(settings.RESULTS_DIR)
        results_dir.mkdir(parents=True, exist_ok=True)
        result_path = results_dir / f"{job_id}.stl"
        solver.export_result(result, str(result_path))

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["result"] = {
            "result_id": job_id,
            "result_path": str(result_path),
            "final_compliance": result.get("compliance", 0.0),
            "iterations": result.get("iterations", 0),
        }

        return OptimizationResponse(
            job_id=job_id,
            status="completed",
            result=jobs[job_id]["result"],
        )

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/status", response_model=OptimizationStatus)
async def get_job_status(job_id: str):
    """Get the status of an optimization job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return OptimizationStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        result=job.get("result"),
        error=job.get("error"),
    )


@router.get("/{job_id}/result/download")
async def download_result(job_id: str):
    """Download the optimized geometry result."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "completed" or not job.get("result"):
        raise HTTPException(status_code=400, detail="Result not available yet")

    result_path = Path(job["result"]["result_path"])
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(result_path),
        filename=f"optimized_{job_id}.stl",
        media_type="application/octet-stream"
    )
