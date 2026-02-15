"""Geometry import/export endpoints."""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.core.config import settings
from app.services.geometry_service import GeometryService
from app.models.geometry import GeometryResponse, GeometryListResponse

router = APIRouter()
geometry_service = GeometryService()


@router.post("/upload", response_model=GeometryResponse)
async def upload_geometry(file: UploadFile = File(...)):
    """Upload a 3D geometry file (STL, OBJ, glTF)."""
    # Validate file extension
    allowed_extensions = {".stl", ".obj", ".gltf", ".glb"}
    ext = Path(file.filename).suffix.lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file
    file_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{file_id}{ext}"

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Parse geometry
        geometry_data = geometry_service.parse_geometry(str(file_path), ext)
        geometry_data["id"] = file_id
        geometry_data["filename"] = file.filename

        logger.info(f"Uploaded geometry: {file.filename} ({ext}) -> {file_id}")
        return GeometryResponse(**geometry_data)

    except Exception as e:
        # Cleanup on error
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=GeometryListResponse)
async def list_geometries():
    """List all uploaded geometries."""
    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.exists():
        return GeometryListResponse(geometries=[])

    geometries = []
    for f in upload_dir.iterdir():
        if f.suffix.lower() in {".stl", ".obj", ".gltf", ".glb"}:
            geometries.append({
                "id": f.stem,
                "filename": f.name,
                "format": f.suffix.lower(),
                "size_bytes": f.stat().st_size,
            })

    return GeometryListResponse(geometries=geometries)


@router.get("/{geometry_id}/mesh")
async def get_mesh_data(geometry_id: str):
    """Get mesh data (vertices, faces) for the 3D viewer."""
    upload_dir = Path(settings.UPLOAD_DIR)

    # Find the file
    for f in upload_dir.iterdir():
        if f.stem == geometry_id:
            mesh_data = geometry_service.get_mesh_data(str(f), f.suffix.lower())
            return mesh_data

    raise HTTPException(status_code=404, detail="Geometry not found")


@router.get("/{geometry_id}/download")
async def download_geometry(geometry_id: str, format: str = "stl"):
    """Download geometry in specified format."""
    upload_dir = Path(settings.UPLOAD_DIR)

    for f in upload_dir.iterdir():
        if f.stem == geometry_id:
            return FileResponse(
                path=str(f),
                filename=f.name,
                media_type="application/octet-stream"
            )

    raise HTTPException(status_code=404, detail="Geometry not found")


@router.delete("/{geometry_id}")
async def delete_geometry(geometry_id: str):
    """Delete an uploaded geometry."""
    upload_dir = Path(settings.UPLOAD_DIR)

    for f in upload_dir.iterdir():
        if f.stem == geometry_id:
            f.unlink()
            logger.info(f"Deleted geometry: {geometry_id}")
            return {"status": "deleted", "id": geometry_id}

    raise HTTPException(status_code=404, detail="Geometry not found")
