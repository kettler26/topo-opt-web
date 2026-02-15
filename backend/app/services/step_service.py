"""
STEP file service — Import/Export via pythonocc (OpenCascade).
Handles STEP ↔ mesh conversion and geometry interrogation.
"""
import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

try:
    from OCP.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID
    from OCP.BRep import BRep_Tool
    from OCP.TopoDS import topods
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import brepgprop
    from OCP.TopLoc import TopLoc_Location
    from OCP.gp import gp_Pnt
    HAS_OCC = True
except ImportError:
    HAS_OCC = False


class StepService:
    """Service for STEP file operations using OpenCascade."""

    def __init__(self):
        if not HAS_OCC:
            print("WARNING: pythonocc/OCP not available. STEP support disabled.")
            print("Install with: pip install cadquery or conda install -c conda-forge pythonocc-core")

    @property
    def available(self) -> bool:
        return HAS_OCC

    def import_step(self, file_path: str) -> dict:
        """
        Import a STEP file and return shape info + tessellated mesh.

        Returns:
            dict with keys: vertices, faces, normals, shape_info, named_selections
        """
        if not HAS_OCC:
            raise RuntimeError("STEP support not available. Install pythonocc.")

        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)

        if status != 1:  # IFSelect_RetDone
            raise ValueError(f"Failed to read STEP file: status {status}")

        reader.TransferRoots()
        shape = reader.OneShape()

        # Tessellate
        mesh = BRepMesh_IncrementalMesh(shape, 0.1, False, 0.5, True)
        mesh.Perform()

        # Extract mesh data
        vertices, faces, normals = self._extract_mesh(shape)

        # Get shape info
        shape_info = self._get_shape_info(shape)

        # Extract named selections from STEP entities
        named_selections = self._extract_named_selections(reader, shape)

        return {
            "vertices": vertices,
            "faces": faces,
            "normals": normals,
            "shape_info": shape_info,
            "named_selections": named_selections,
        }

    def export_step(self, shape_or_mesh: dict, output_path: str) -> str:
        """
        Export geometry as STEP file.
        For mesh-only data, creates a shell from triangulation.
        """
        if not HAS_OCC:
            raise RuntimeError("STEP support not available.")

        writer = STEPControl_Writer()

        if hasattr(shape_or_mesh, 'ShapeType'):
            # It's an OCC shape
            writer.Transfer(shape_or_mesh, STEPControl_AsIs)
        else:
            raise ValueError("Direct mesh-to-STEP export requires shape reconstruction (Phase 3)")

        status = writer.Write(output_path)
        if status != 1:
            raise RuntimeError(f"Failed to write STEP file: status {status}")

        return output_path

    def step_to_stl(self, step_path: str, stl_path: str, linear_deflection: float = 0.1) -> str:
        """Convert STEP to STL via tessellation."""
        if not HAS_OCC:
            raise RuntimeError("STEP support not available.")

        reader = STEPControl_Reader()
        reader.ReadFile(step_path)
        reader.TransferRoots()
        shape = reader.OneShape()

        mesh = BRepMesh_IncrementalMesh(shape, linear_deflection, False, 0.5, True)
        mesh.Perform()

        writer = StlAPI_Writer()
        writer.Write(shape, stl_path)

        return stl_path

    def _extract_mesh(self, shape) -> tuple:
        """Extract triangulated mesh from tessellated shape."""
        vertices = []
        faces = []
        normals = []
        vertex_offset = 0

        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = topods.Face(explorer.Current())
            location = TopLoc_Location()
            triangulation = BRep_Tool.Triangulation(face, location)

            if triangulation is not None:
                nb_nodes = triangulation.NbNodes()
                nb_triangles = triangulation.NbTriangles()

                # Vertices
                for i in range(1, nb_nodes + 1):
                    pnt = triangulation.Node(i)
                    if not location.IsIdentity():
                        pnt = pnt.Transformed(location.Transformation())
                    vertices.extend([pnt.X(), pnt.Y(), pnt.Z()])

                # Faces (triangles)
                for i in range(1, nb_triangles + 1):
                    tri = triangulation.Triangle(i)
                    n1, n2, n3 = tri.Get()
                    faces.extend([
                        n1 - 1 + vertex_offset,
                        n2 - 1 + vertex_offset,
                        n3 - 1 + vertex_offset,
                    ])

                # Normals (approximate from face)
                for i in range(nb_nodes):
                    normals.extend([0.0, 1.0, 0.0])  # Placeholder

                vertex_offset += nb_nodes

            explorer.Next()

        return vertices, faces, normals

    def _get_shape_info(self, shape) -> dict:
        """Get geometric properties of the shape."""
        info = {"faces": 0, "edges": 0, "vertices": 0, "solids": 0}

        for topo_type, key in [
            (TopAbs_FACE, "faces"),
            (TopAbs_EDGE, "edges"),
            (TopAbs_VERTEX, "vertices"),
            (TopAbs_SOLID, "solids"),
        ]:
            explorer = TopExp_Explorer(shape, topo_type)
            count = 0
            while explorer.More():
                count += 1
                explorer.Next()
            info[key] = count

        # Volume and surface area
        props = GProp_GProps()
        brepgprop.VolumeProperties(shape, props)
        info["volume"] = props.Mass()

        brepgprop.SurfaceProperties(shape, props)
        info["surface_area"] = props.Mass()

        return info

    def _extract_named_selections(self, reader, shape) -> list:
        """Extract named entities from STEP file as named selections."""
        selections = []
        # STEP files can contain named entities — extract them
        # This is a simplified version; full implementation would use
        # XDE (Extended Data Exchange) framework
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        face_idx = 0
        while explorer.More():
            selections.append({
                "id": f"face_{face_idx}",
                "name": f"Fläche {face_idx + 1}",
                "type": "face",
                "entity_indices": [face_idx],
            })
            face_idx += 1
            explorer.Next()

        return selections
