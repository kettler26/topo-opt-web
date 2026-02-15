"""
Geometry API — Import/Export 3D models (STL, OBJ, glTF, STEP).
Phase 2: Added STEP support, named selections, mesh refinement.
"""
import os
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

from app.services.mesh_service import MeshService
from app.services.step_service import StepService
from app.services.mesh_refinement import MeshRefinementService, RefinementConfig
from app.models.named_selections import NamedSelection, NamedSelectionSet

router = APIRouter()
mesh_service = MeshService()
step_service = StepService()
refinement_service = MeshRefinementService()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
RESULT_DIR = Path(os.getenv("RESULT_DIR", "results"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".stl", ".obj", ".gltf", ".glb", ".step", ".stp"}

# In-memory store for named selections (per file)
_named_selections: dict[str, NamedSelectionSet] = {}


@router.post("/upload")
async def upload_geometry(file: UploadFile = File(...)):
    """Upload a 3D geometry file (STL, OBJ, glTF, STEP)."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht unterstütztes Format: {ext}. Erlaubt: {ALLOWED_EXTENSIONS}",
        )

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{ext}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse based on format
    if ext in {".step", ".stp"}:
        if not step_service.available:
            # Fallback: save file but note STEP processing unavailable
            return {
                "file_id": file_id,
                "filename": file.filename,
                "format": ext,
                "mesh_info": {"error": "STEP-Verarbeitung nicht verfügbar. pythonocc installieren."},
                "named_selections": [],
            }
        step_data = step_service.import_step(str(file_path))
        mesh_info = step_data["shape_info"]
        named_sels = [NamedSelection(**s, entity_type="face") for s in step_data["named_selections"]]
        _named_selections[file_id] = NamedSelectionSet(selections=named_sels)
    else:
        mesh_info = mesh_service.get_mesh_info(str(file_path))
        _named_selections[file_id] = NamedSelectionSet()

    return {
        "file_id": file_id,
        "filename": file.filename,
        "format": ext,
        "mesh_info": mesh_info,
        "named_selections": [s.model_dump() for s in _named_selections[file_id].selections],
    }


@router.get("/{file_id}/info")
async def get_geometry_info(file_id: str):
    """Get mesh information and named selections."""
    file_path = _find_file(UPLOAD_DIR, file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Geometrie nicht gefunden")

    mesh_info = mesh_service.get_mesh_info(str(file_path))
    selections = _named_selections.get(file_id, NamedSelectionSet())

    return {
        "file_id": file_id,
        "mesh_info": mesh_info,
        "named_selections": [s.model_dump() for s in selections.selections],
    }


@router.get("/{file_id}/download")
async def download_geometry(file_id: str, format: str = "stl"):
    """Download geometry in specified format."""
    file_path = _find_file(UPLOAD_DIR, file_id) or _find_file(RESULT_DIR, file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Geometrie nicht gefunden")
    return FileResponse(
        path=str(file_path),
        filename=f"geometry_{file_id}{Path(file_path).suffix}",
        media_type="application/octet-stream",
    )


@router.post("/{file_id}/export")
async def export_geometry(file_id: str, target_format: str = "stl"):
    """Export/convert geometry to a different format."""
    file_path = _find_file(UPLOAD_DIR, file_id) or _find_file(RESULT_DIR, file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Geometrie nicht gefunden")

    target_ext = f".{target_format.lower()}"
    if target_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Nicht unterstütztes Zielformat: {target_format}")

    export_id = str(uuid.uuid4())
    export_path = RESULT_DIR / f"{export_id}{target_ext}"

    src_ext = Path(file_path).suffix.lower()

    # Handle STEP conversions
    if src_ext in {".step", ".stp"} and target_ext == ".stl":
        step_service.step_to_stl(str(file_path), str(export_path))
    elif target_ext in {".step", ".stp"}:
        raise HTTPException(status_code=400, detail="Mesh → STEP Export kommt in Phase 3")
    else:
        mesh_service.convert(str(file_path), str(export_path))

    return {
        "file_id": export_id,
        "source_format": src_ext,
        "export_format": target_format,
        "download_url": f"/api/geometry/{export_id}/download",
    }


# ==========================================
# Named Selections API
# ==========================================

@router.get("/{file_id}/selections")
async def get_named_selections(file_id: str):
    """Get all named selections for a geometry."""
    selections = _named_selections.get(file_id, NamedSelectionSet())
    return {"selections": [s.model_dump() for s in selections.selections]}


@router.post("/{file_id}/selections")
async def create_named_selection(file_id: str, selection: NamedSelection):
    """Create a new named selection."""
    if file_id not in _named_selections:
        _named_selections[file_id] = NamedSelectionSet()
    _named_selections[file_id].selections.append(selection)
    return {"selection": selection.model_dump()}


@router.delete("/{file_id}/selections/{selection_id}")
async def delete_named_selection(file_id: str, selection_id: str):
    """Delete a named selection."""
    if file_id not in _named_selections:
        raise HTTPException(status_code=404, detail="Keine Selektionen gefunden")
    sels = _named_selections[file_id]
    sels.selections = [s for s in sels.selections if s.id != selection_id]
    return {"deleted": selection_id}


# ==========================================
# Mesh Refinement API
# ==========================================

@router.post("/{file_id}/refine")
async def refine_mesh(file_id: str, config: RefinementConfig):
    """Refine mesh with given configuration."""
    file_path = _find_file(UPLOAD_DIR, file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Geometrie nicht gefunden")

    try:
        mesh = mesh_service.load_mesh(str(file_path))
        stats_before = refinement_service.get_mesh_stats(mesh)

        refined = refinement_service.refine(mesh, config)

        # Save refined mesh
        refined_id = str(uuid.uuid4())
        refined_path = RESULT_DIR / f"{refined_id}.stl"
        refined.export(str(refined_path), file_type="stl")

        stats_after = refinement_service.get_mesh_stats(refined)

        return {
            "refined_file_id": refined_id,
            "stats_before": stats_before,
            "stats_after": stats_after,
            "download_url": f"/api/geometry/{refined_id}/download",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verfeinerung fehlgeschlagen: {str(e)}")


@router.get("/{file_id}/mesh-stats")
async def get_mesh_stats(file_id: str):
    """Get detailed mesh quality statistics."""
    file_path = _find_file(UPLOAD_DIR, file_id) or _find_file(RESULT_DIR, file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Geometrie nicht gefunden")
    try:
        mesh = mesh_service.load_mesh(str(file_path))
        return refinement_service.get_mesh_stats(mesh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _find_file(directory: Path, file_id: str) -> Path | None:
    for f in directory.iterdir():
        if f.stem.startswith(file_id):
            return f
    return None
