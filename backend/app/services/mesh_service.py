"""Mesh service for loading, inspecting and converting geometry files."""
from pathlib import Path

import trimesh


class MeshService:
    """Utility wrapper around trimesh for mesh operations."""

    def load_mesh(self, file_path: str) -> trimesh.Trimesh:
        loaded = trimesh.load(file_path)
        if isinstance(loaded, trimesh.Scene):
            mesh = loaded.dump(concatenate=True)
        else:
            mesh = loaded
        if not isinstance(mesh, trimesh.Trimesh):
            raise ValueError("Datei enthält kein gültiges Mesh")
        return mesh

    def get_mesh_info(self, file_path: str) -> dict:
        mesh = self.load_mesh(file_path)
        bounds = mesh.bounds
        return {
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "num_vertices": int(len(mesh.vertices)),
            "num_faces": int(len(mesh.faces)),
            "is_watertight": bool(mesh.is_watertight),
            "volume": float(mesh.volume) if mesh.is_watertight else None,
            "surface_area": float(mesh.area),
            "bounds_min": bounds[0].tolist(),
            "bounds_max": bounds[1].tolist(),
            "center": mesh.centroid.tolist() if mesh.vertices.size else [0, 0, 0],
        }

    def convert(self, source_path: str, target_path: str) -> None:
        mesh = self.load_mesh(source_path)
        ext = Path(target_path).suffix.lower()
        file_type = "glb" if ext == ".glb" else ext.replace(".", "")
        mesh.export(target_path, file_type=file_type)


    def get_mesh_data(self, file_path: str) -> dict:
        mesh = self.load_mesh(file_path)
        return {
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "normals": mesh.face_normals.tolist(),
        }
