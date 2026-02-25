"""Optimization API with async job queue and progress tracking."""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.optimizer import SIMPOptimizer, OptimizationConfig
from app.models.boundary_conditions import BoundaryConditionSet
from app.models.contact_conditions import ContactConditionSet

router = APIRouter()
optimizer = SIMPOptimizer(queue_limit=2)
UPLOAD_DIR = Path("uploads")
RESULT_DIR = Path("results")
RESULT_DIR.mkdir(parents=True, exist_ok=True)


class OptimizationRequest(BaseModel):
    file_id: str = Field(..., description="ID of uploaded geometry")
    volume_fraction: float = Field(0.4, ge=0.01, le=0.99)
    penalty: float = Field(3.0, ge=1.0, le=5.0)
    filter_radius: float = Field(1.5, ge=0.1)
    max_iterations: int = Field(100, ge=1, le=1000)
    tolerance: float = Field(1e-4, ge=1e-8)
    boundary_conditions: Optional[BoundaryConditionSet] = None
    contact_conditions: Optional[ContactConditionSet] = None
    frozen_selection_ids: List[str] = Field(default_factory=list)
    symmetry_planes: List[str] = Field(default_factory=list)


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


_jobs: dict[str, dict] = {}
_tasks: dict[str, asyncio.Task] = {}


def _find_file(file_id: str) -> Path | None:
    for directory in (UPLOAD_DIR, RESULT_DIR):
        for path in directory.glob(f"{file_id}*"):
            return path
    return None


async def _run_job(job_id: str) -> None:
    job = _jobs[job_id]
    file_path = _find_file(job["file_id"])
    if not file_path:
        job["status"] = "failed"
        job["message"] = "Geometrie nicht gefunden"
        return

    if job["status"] == "cancelled":
        return

    job["status"] = "running"
    job["message"] = "Solver läuft"

    result_file_id = str(uuid.uuid4())
    result_path = RESULT_DIR / f"{result_file_id}.stl"

    try:
        result = await optimizer.run(
            file_path=file_path,
            result_path=result_path,
            config=job["config"],
            boundary_conditions=[bc.model_dump() for bc in (job["boundary_conditions"].conditions if job["boundary_conditions"] else [])],
        )
        if job["status"] == "cancelled":
            if result_path.exists():
                result_path.unlink(missing_ok=True)
            return

        job["status"] = "completed"
        job["message"] = "Optimierung abgeschlossen"
        job["iteration"] = int(result.get("iterations", 0))
        job["compliance"] = float(result.get("compliance", 0.0))
        job["change"] = 0.0
        job["result_file_id"] = result_file_id
    except asyncio.CancelledError:
        job["status"] = "cancelled"
        job["message"] = "Job abgebrochen"
    except Exception as exc:
        job["status"] = "failed"
        job["message"] = f"Optimierung fehlgeschlagen: {exc}"
    finally:
        _tasks.pop(job_id, None)


@router.post("/run", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    config = OptimizationConfig(
        volume_fraction=request.volume_fraction,
        penalty=request.penalty,
        filter_radius=request.filter_radius,
        max_iterations=request.max_iterations,
        tolerance=request.tolerance,
    )
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "queued",
        "message": "In Warteschlange",
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
    _tasks[job_id] = asyncio.create_task(_run_job(job_id))
    return OptimizationResponse(job_id=job_id, status="queued", message="Job erstellt")


@router.get("/{job_id}/status", response_model=OptimizationStatus)
async def get_optimization_status(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    job = _jobs[job_id]
    return OptimizationStatus(
        job_id=job_id,
        status=job["status"],
        iteration=job["iteration"],
        max_iterations=job["config"].max_iterations,
        compliance=job["compliance"],
        volume_fraction=job["config"].volume_fraction,
        change=job["change"],
        message=job["message"],
        result_file_id=job["result_file_id"],
    )


@router.get("/{job_id}/result/download")
async def download_optimization_result(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")

    result_file_id = _jobs[job_id].get("result_file_id")
    if not result_file_id:
        raise HTTPException(status_code=409, detail="Ergebnis noch nicht verfügbar")

    file_path = _find_file(result_file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Ergebnisdatei nicht gefunden")

    return FileResponse(path=str(file_path), filename=f"optimization_{job_id}.stl", media_type="application/octet-stream")


@router.post("/{job_id}/cancel")
async def cancel_optimization(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job nicht gefunden")
    if _jobs[job_id]["status"] in {"completed", "failed", "cancelled"}:
        return {"job_id": job_id, "status": _jobs[job_id]["status"]}

    _jobs[job_id]["status"] = "cancelled"
    _jobs[job_id]["message"] = "Manuell abgebrochen"

    task = _tasks.get(job_id)
    if task and not task.done():
        task.cancel()

    return {"job_id": job_id, "status": "cancelled"}


@router.get("/jobs")
async def list_jobs():
    return {
        "jobs": [
            {
                "job_id": jid,
                "status": j["status"],
                "file_id": j["file_id"],
                "iteration": j["iteration"],
            }
            for jid, j in _jobs.items()
        ]
    }
