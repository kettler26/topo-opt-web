"""Optimization orchestration service with a lightweight async job queue."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.solver.simp import SIMPSolver


@dataclass
class OptimizationConfig:
    volume_fraction: float = 0.4
    penalty: float = 3.0
    filter_radius: float = 1.5
    max_iterations: int = 100
    tolerance: float = 1e-4


class SIMPOptimizer:
    def __init__(self, queue_limit: int = 2):
        self._sem = asyncio.Semaphore(queue_limit)

    async def run(self, file_path: Path, result_path: Path, config: OptimizationConfig, boundary_conditions: list[dict[str, Any]]) -> dict[str, Any]:
        async with self._sem:
            solver = SIMPSolver(
                volume_fraction=config.volume_fraction,
                penalty=config.penalty,
                filter_radius=config.filter_radius,
                max_iterations=config.max_iterations,
                tolerance=config.tolerance,
            )
            result = await asyncio.to_thread(solver.optimize, str(file_path), boundary_conditions)
            await asyncio.to_thread(solver.export_result, result, str(result_path))
            return result
