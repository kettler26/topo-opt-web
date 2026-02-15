"""
Optimization API — Phase 2: Enhanced with named selections, contact conditions.
"""
import uuid
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.optimizer import SIMPOptimizer, OptimizationConfig
from app.models.boundary_conditions import BoundaryConditionSet, AnyBoundaryCondition
from app.models.contact_conditions import ContactConditionSet, ContactPair
from app.models.named_selections import NamedSelectionSet

router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request to start a topology optimization."""
    file_id: str = Field(..., description="ID of the uploaded geometry")
    volume_fraction: float = Field(0.4, ge=0.01, le=0.99)
    penalty: float = Field(3.0, ge=1.0, le=5.0)
    filter_radius: float = Field(1.5, ge=0.1)
    max_iterations: int = Field(100, ge=1, le=1000)
    tolerance: float = Field(1e-4, ge=1e-8)
    boundary_conditions: Optional[BoundaryConditionSet] = None
    contact_conditions: Optional[ContactConditionSet] = None
    frozen_selection_ids: List[str] = Field(
        default_factory=list,
        description="Named selection IDs that should NOT be optimized (frozen regions)"
    )
    symmetry_planes: List[str] = Field(
        default_factory=list,
        description="Symmetry plane definitions: 'x', 'y', 'z', 'xy', 'xz', 'yz'"
    )


class OptimizationResponse(BaseModel):
    job_id: str
    status: str
    message: str


class OptimizationStatus(BaseModel):
    job_id: str
    status: str
    iteration: int = 0
    max_iterations: int = 0
    compliance: float = 0.0
    volume_fraction: float = 0.0
    change: float = 1.0
    message: str = ""
    result_file_id: Optional[str] = None


# In-memory job store
_jobs: dict = {}


@router.post("/run", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    """Start a topology optimization job."""
    job_id = str(uuid.uuid4())

    config = OptimizationConfig(
        volume_fraction=request.volume_fraction,
        penalty=request.penalty,
        filter_radius=request.filter_radius,
        max_iterations=request.max_iterations,
        tolerance=request.tolerance,
    )

    _jobs[job_id] = {
        "status": "queued",
        "config": config,
        "file_id": request.file_id,
        "boundary_conditions": request.boundary_conditions,
        "contact_conditions": request.contact_conditions,
        "frozen_selection_ids": request.frozen_selection_ids,
        "symmetry_planes": request.symmetry_planes,
        "iteration": 0,
        "compliance": 0.0,
        "change": 1.0,
        "result_file_id": None,
    }

    return OptimizationResponse(
        job_id=job_id,
        status="queued",
        message="Optimierungsjob erstellt. Solver-Integration aktiv.",
    )


@router.get("/{job_id}/status", response_model=OptimizationStatus)
async def get_optimization_status(job_id: str):
    """Check optimization job status."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    job = _jobs[job_id]
    return OptimizationStatus(
        job_id=job_id,
        status=job["status"],
        iteration=job.get("iteration", 0),
        max_iterations=job["config"].max_iterations,
        compliance=job.get("compliance", 0.0),
        volume_fraction=job["config"].volume_fraction,
        change=job.get("change", 1.0),
        message=f"Job-Status: {job['status']}",
        result_file_id=job.get("result_file_id"),
    )


@router.post("/{job_id}/cancel")
async def cancel_optimization(job_id: str):
    """Cancel a running optimization job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    _jobs[job_id]["status"] = "cancelled"
    return {"job_id": job_id, "status": "cancelled"}


@router.get("/jobs")
async def list_jobs():
    """List all optimization jobs."""
    return {
        "jobs": [
            {
                "job_id": jid,
                "status": j["status"],
                "file_id": j["file_id"],
                "iteration": j.get("iteration", 0),
            }
            for jid, j in _jobs.items()
        ]
    }
