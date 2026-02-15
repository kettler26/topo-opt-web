"""Optimization data models."""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class BoundaryCondition(BaseModel):
    """A single boundary condition."""
    type: Literal["fixation", "force", "pressure", "temperature"]
    name: str = "Unnamed BC"
    # Selection: face indices or vertex indices
    selection_type: Literal["faces", "vertices"] = "faces"
    selection_ids: list[int] = []
    # Force vector (for type='force')
    force_vector: Optional[list[float]] = None  # [fx, fy, fz] in N
    # Pressure value (for type='pressure')
    pressure_value: Optional[float] = None  # in Pa
    # Temperature value (for type='temperature')
    temperature_value: Optional[float] = None  # in K
    # Fixation DOFs (for type='fixation')
    fixed_dofs: list[str] = Field(default_factory=lambda: ["x", "y", "z"])


class OptimizationRequest(BaseModel):
    """Request to start an optimization."""
    geometry_id: str
    boundary_conditions: list[BoundaryCondition]
    volume_fraction: float = Field(default=0.4, ge=0.01, le=0.99)
    penalty: float = Field(default=3.0, ge=1.0, le=5.0)
    filter_radius: float = Field(default=1.5, ge=0.1, le=10.0)
    max_iterations: int = Field(default=200, ge=1, le=1000)
    mesh_resolution: int = Field(default=30, ge=5, le=200)


class OptimizationResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None


class OptimizationStatus(BaseModel):
    job_id: str
    status: str  # "running", "completed", "failed"
    progress: float = 0.0
    result: Optional[dict] = None
    error: Optional[str] = None
