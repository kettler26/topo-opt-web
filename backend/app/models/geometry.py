"""Geometry data models."""
from pydantic import BaseModel
from typing import Optional


class GeometryResponse(BaseModel):
    id: str
    filename: str
    format: str
    vertices_count: int = 0
    faces_count: int = 0
    bounding_box: Optional[dict] = None
    volume: Optional[float] = None


class GeometryListItem(BaseModel):
    id: str
    filename: str
    format: str
    size_bytes: int = 0


class GeometryListResponse(BaseModel):
    geometries: list[GeometryListItem]
