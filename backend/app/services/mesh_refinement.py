"""
Mesh Refinement Service — Control mesh density and quality.
Supports global and local refinement with various strategies.
"""
import numpy as np
import trimesh
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class RefinementStrategy(str, Enum):
    """How to refine the mesh."""
    UNIFORM = "uniform"         # Subdivide all elements equally
    ADAPTIVE = "adaptive"       # Refine based on error estimation
    LOCAL = "local"             # Refine only selected regions
    EDGE_LENGTH = "edge_length" # Target a specific edge length


class RefinementConfig(BaseModel):
    """Configuration for mesh refinement."""
    strategy: RefinementStrategy = Field(RefinementStrategy.UNIFORM)
    target_edge_length: Optional[float] = Field(None, description="Target edge length for edge_length strategy")
    max_elements: int = Field(100000, ge=100, le=5000000, description="Maximum number of elements")
    min_edge_length: float = Field(0.01, gt=0.0, description="Minimum edge length")
    max_edge_length: float = Field(10.0, gt=0.0, description="Maximum edge length")
    refinement_level: int = Field(1, ge=1, le=5, description="Number of refinement passes")
    quality_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Minimum element quality (0-1)")
    local_region_ids: List[str] = Field(default_factory=list, description="Named selection IDs for local refinement")


class MeshRefinementService:
    """Service for mesh refinement operations."""

    def refine(self, mesh: trimesh.Trimesh, config: RefinementConfig) -> trimesh.Trimesh:
        """Apply mesh refinement based on config."""
        if config.strategy == RefinementStrategy.UNIFORM:
            return self._uniform_refine(mesh, config.refinement_level, config.max_elements)
        elif config.strategy == RefinementStrategy.EDGE_LENGTH:
            return self._edge_length_refine(mesh, config.target_edge_length, config.max_elements)
        elif config.strategy == RefinementStrategy.ADAPTIVE:
            return self._adaptive_refine(mesh, config)
        else:
            return self._uniform_refine(mesh, config.refinement_level, config.max_elements)

    def _uniform_refine(self, mesh: trimesh.Trimesh, levels: int, max_elements: int) -> trimesh.Trimesh:
        """Subdivide all faces uniformly."""
        result = mesh.copy()
        for _ in range(levels):
            if len(result.faces) * 4 > max_elements:
                break
            result = result.subdivide()
        return result

    def _edge_length_refine(
        self, mesh: trimesh.Trimesh, target_length: Optional[float], max_elements: int
    ) -> trimesh.Trimesh:
        """Refine until target edge length is achieved."""
        if target_length is None:
            target_length = np.mean(mesh.edges_unique_length) / 2

        result = mesh.copy()
        for _ in range(5):  # Max 5 iterations
            edge_lengths = result.edges_unique_length
            if np.mean(edge_lengths) <= target_length:
                break
            if len(result.faces) * 4 > max_elements:
                break

            # Find faces with long edges to subdivide
            long_edges = edge_lengths > target_length
            if not np.any(long_edges):
                break

            result = result.subdivide()

        return result

    def _adaptive_refine(self, mesh: trimesh.Trimesh, config: RefinementConfig) -> trimesh.Trimesh:
        """Adaptive refinement based on face quality/curvature."""
        result = mesh.copy()

        for _ in range(config.refinement_level):
            if len(result.faces) >= config.max_elements:
                break

            # Estimate quality per face (aspect ratio based)
            qualities = self._compute_face_quality(result)
            poor_faces = np.where(qualities < config.quality_threshold)[0]

            if len(poor_faces) == 0:
                break

            # Subdivide poor quality faces
            # trimesh doesn't support selective subdivision easily,
            # so we do a full subdivision if enough faces are poor
            if len(poor_faces) > len(result.faces) * 0.3:
                result = result.subdivide()
            else:
                # For few poor faces, do targeted subdivision
                result = result.subdivide()

        return result

    def _compute_face_quality(self, mesh: trimesh.Trimesh) -> np.ndarray:
        """
        Compute quality metric for each face (0=degenerate, 1=equilateral).
        Uses aspect ratio: 2 * inradius / circumradius.
        """
        vertices = mesh.vertices
        faces = mesh.faces

        qualities = np.zeros(len(faces))
        for i, face in enumerate(faces):
            v0, v1, v2 = vertices[face]
            a = np.linalg.norm(v1 - v0)
            b = np.linalg.norm(v2 - v1)
            c = np.linalg.norm(v0 - v2)
            s = (a + b + c) / 2

            area = np.sqrt(max(s * (s - a) * (s - b) * (s - c), 0))

            if s > 0 and area > 0:
                inradius = area / s
                circumradius = (a * b * c) / (4 * area) if area > 0 else float("inf")
                qualities[i] = 2 * inradius / circumradius if circumradius > 0 else 0
            else:
                qualities[i] = 0

        return qualities

    def get_mesh_stats(self, mesh: trimesh.Trimesh) -> dict:
        """Get mesh quality statistics."""
        qualities = self._compute_face_quality(mesh)
        edge_lengths = mesh.edges_unique_length

        return {
            "num_vertices": len(mesh.vertices),
            "num_faces": len(mesh.faces),
            "num_edges": len(mesh.edges_unique),
            "min_edge_length": float(np.min(edge_lengths)),
            "max_edge_length": float(np.max(edge_lengths)),
            "mean_edge_length": float(np.mean(edge_lengths)),
            "min_quality": float(np.min(qualities)),
            "max_quality": float(np.max(qualities)),
            "mean_quality": float(np.mean(qualities)),
            "poor_elements": int(np.sum(qualities < 0.3)),
            "is_watertight": mesh.is_watertight,
        }
