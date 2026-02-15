"""Geometry parsing and conversion service."""
import numpy as np
from pathlib import Path
from loguru import logger


class GeometryService:
    """Handles geometry file parsing, conversion, and mesh data extraction."""

    def parse_geometry(self, file_path: str, extension: str) -> dict:
        """Parse a geometry file and return metadata."""
        ext = extension.lower()

        if ext == ".stl":
            return self._parse_stl(file_path)
        elif ext in (".obj",):
            return self._parse_obj(file_path)
        elif ext in (".gltf", ".glb"):
            return self._parse_gltf(file_path)
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _parse_stl(self, file_path: str) -> dict:
        """Parse STL file using numpy-stl."""
        from stl import mesh as stl_mesh

        stl = stl_mesh.Mesh.from_file(file_path)
        vertices = stl.vectors.reshape(-1, 3)
        unique_vertices = np.unique(vertices, axis=0)

        bbox = {
            "min": vertices.min(axis=0).tolist(),
            "max": vertices.max(axis=0).tolist(),
        }

        # Approximate volume using signed volume method
        volume = float(abs(stl.get_mass_properties()[0]))

        return {
            "format": ".stl",
            "vertices_count": len(unique_vertices),
            "faces_count": len(stl.vectors),
            "bounding_box": bbox,
            "volume": volume,
        }

    def _parse_obj(self, file_path: str) -> dict:
        """Parse OBJ file using trimesh."""
        import trimesh

        mesh = trimesh.load(file_path)
        bbox = {
            "min": mesh.bounds[0].tolist(),
            "max": mesh.bounds[1].tolist(),
        }

        return {
            "format": ".obj",
            "vertices_count": len(mesh.vertices),
            "faces_count": len(mesh.faces),
            "bounding_box": bbox,
            "volume": float(mesh.volume) if mesh.is_watertight else None,
        }

    def _parse_gltf(self, file_path: str) -> dict:
        """Parse glTF/GLB file using trimesh."""
        import trimesh

        scene = trimesh.load(file_path)
        if isinstance(scene, trimesh.Scene):
            mesh = scene.dump(concatenate=True)
        else:
            mesh = scene

        bbox = {
            "min": mesh.bounds[0].tolist(),
            "max": mesh.bounds[1].tolist(),
        }

        return {
            "format": Path(file_path).suffix.lower(),
            "vertices_count": len(mesh.vertices),
            "faces_count": len(mesh.faces),
            "bounding_box": bbox,
            "volume": float(mesh.volume) if mesh.is_watertight else None,
        }

    def get_mesh_data(self, file_path: str, extension: str) -> dict:
        """Get mesh vertices and faces for the 3D viewer."""
        ext = extension.lower()

        if ext == ".stl":
            from stl import mesh as stl_mesh
            stl = stl_mesh.Mesh.from_file(file_path)
            vertices = stl.vectors.reshape(-1, 3)
            # Build face indices (every 3 vertices form a face)
            faces = np.arange(len(vertices)).reshape(-1, 3)
            normals = stl.normals.tolist()
        else:
            import trimesh
            loaded = trimesh.load(file_path)
            if isinstance(loaded, trimesh.Scene):
                loaded = loaded.dump(concatenate=True)
            vertices = loaded.vertices
            faces = loaded.faces
            normals = loaded.face_normals.tolist()

        return {
            "vertices": vertices.tolist(),
            "faces": faces.tolist(),
            "normals": normals,
        }
