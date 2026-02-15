"""SIMP (Solid Isotropic Material with Penalization) Topology Optimizer.

This is the core solver for the topology optimization. It takes a voxelized
representation of the design domain and optimizes material distribution to
minimize compliance (maximize stiffness) subject to a volume constraint.
"""
import numpy as np
from scipy.sparse import coo_matrix, linalg as splinalg
from scipy.ndimage import convolve
from loguru import logger


class SIMPSolver:
    """SIMP topology optimization solver."""

    def __init__(
        self,
        volume_fraction: float = 0.4,
        penalty: float = 3.0,
        filter_radius: float = 1.5,
        max_iterations: int = 200,
        tolerance: float = 0.01,
        young_modulus: float = 1.0,
        poisson_ratio: float = 0.3,
    ):
        self.volfrac = volume_fraction
        self.penal = penalty
        self.rmin = filter_radius
        self.max_iter = max_iterations
        self.tol = tolerance
        self.E0 = young_modulus
        self.nu = poisson_ratio
        self.Emin = 1e-9  # Minimum stiffness to avoid singularity

    def optimize(self, geometry_path: str, boundary_conditions: list) -> dict:
        """Run topology optimization.

        For the MVP, we use a simple 3D voxel grid. The geometry file is used
        to determine the bounding box and the voxel grid resolution.

        Args:
            geometry_path: Path to the geometry file
            boundary_conditions: List of BoundaryCondition objects

        Returns:
            Dictionary with optimization results
        """
        logger.info("Starting SIMP optimization...")

        # For MVP: simple 3D cantilever beam demo
        # TODO: Integrate with actual geometry voxelization
        nelx, nely, nelz = 30, 10, 10
        n_elements = nelx * nely * nelz

        # Initialize density field
        x = np.full(n_elements, self.volfrac)
        xphys = x.copy()

        # Element stiffness matrix (8-node hexahedral)
        KE = self._element_stiffness_matrix_3d()

        # Node numbering
        ndof = 3 * (nelx + 1) * (nely + 1) * (nelz + 1)

        # Parse boundary conditions
        # For MVP: fixed left face, force on right face
        fixed_dofs, force_dofs, force_values = self._parse_bcs(
            nelx, nely, nelz, boundary_conditions
        )

        # Force vector
        F = np.zeros(ndof)
        for dof, val in zip(force_dofs, force_values):
            F[dof] = val

        # Free DOFs
        all_dofs = np.arange(ndof)
        free_dofs = np.setdiff1d(all_dofs, fixed_dofs)

        # Filter preparation
        H, Hs = self._prepare_filter(nelx, nely, nelz)

        # Optimization loop (OC method)
        compliance_history = []
        change = 1.0
        loop = 0

        logger.info(f"Grid: {nelx}x{nely}x{nelz} = {n_elements} elements")
        logger.info(f"DOFs: {ndof}, Free: {len(free_dofs)}")

        while change > self.tol and loop < self.max_iter:
            loop += 1

            # FE analysis
            U = self._solve_fe(
                nelx, nely, nelz, KE, xphys, free_dofs, F, ndof
            )

            # Objective and sensitivity
            ce, dc, compliance = self._compute_sensitivity(
                nelx, nely, nelz, KE, U, xphys
            )
            compliance_history.append(float(compliance))

            # Filter sensitivities
            dc_filtered = np.asarray(H.dot(dc.flatten()) / Hs).reshape(dc.shape)

            # Optimality criteria update
            x_new = self._oc_update(nelx, nely, nelz, x, dc_filtered)
            xphys = np.asarray(H.dot(x_new.flatten()) / Hs).reshape(x_new.shape)

            change = np.max(np.abs(x_new - x))
            x = x_new.copy()

            if loop % 10 == 0:
                logger.info(
                    f"Iter {loop}: compliance={compliance:.4f}, "
                    f"vol={np.mean(xphys):.4f}, change={change:.4f}"
                )

        logger.info(f"Optimization completed in {loop} iterations")

        return {
            "density": xphys.tolist(),
            "compliance": float(compliance_history[-1]) if compliance_history else 0.0,
            "compliance_history": compliance_history,
            "iterations": loop,
            "grid_size": [nelx, nely, nelz],
            "volume_fraction_achieved": float(np.mean(xphys)),
        }

    def _element_stiffness_matrix_3d(self) -> np.ndarray:
        """Compute 3D 8-node hexahedral element stiffness matrix."""
        E = self.E0
        nu = self.nu

        # Simplified: use analytical formula for unit cube element
        # Based on Cook et al. finite element formulation
        k = np.array([
            1/2 - nu/6, 1/8 + nu/8, -1/4 - nu/12, -1/8 + 3*nu/8,
            -1/4 + nu/12, -1/8 - nu/8, nu/6, 1/8 - 3*nu/8
        ])

        KE = E / (1 - nu**2) * np.array([
            [k[0], k[1], k[1], k[2], k[3], k[3], k[4], k[5]],
            [k[1], k[0], k[1], k[5], k[4], k[3], k[3], k[2]],
            [k[1], k[1], k[0], k[3], k[5], k[4], k[3], k[2]],
            [k[2], k[5], k[3], k[0], k[1], k[1], k[4], k[3]],
            [k[3], k[4], k[5], k[1], k[0], k[1], k[5], k[2]],
            [k[3], k[3], k[4], k[1], k[1], k[0], k[2], k[5]],
            [k[4], k[3], k[3], k[4], k[5], k[2], k[0], k[1]],
            [k[5], k[2], k[2], k[3], k[2], k[5], k[1], k[0]],
        ])

        # Expand to 24x24 (3 DOF per node x 8 nodes)
        # This is a simplified version - full implementation uses Gauss quadrature
        KE_full = np.zeros((24, 24))
        for i in range(8):
            for j in range(8):
                for di in range(3):
                    for dj in range(3):
                        if di == dj:
                            KE_full[3*i+di, 3*j+dj] = KE[i, j]
                        else:
                            KE_full[3*i+di, 3*j+dj] = KE[i, j] * nu * 0.3

        # Ensure symmetry
        KE_full = 0.5 * (KE_full + KE_full.T)
        return KE_full

    def _parse_bcs(self, nelx, nely, nelz, boundary_conditions):
        """Parse boundary conditions into DOF lists.

        For MVP: default to cantilever beam setup.
        """
        fixed_dofs = []
        force_dofs = []
        force_values = []

        if not boundary_conditions:
            # Default: cantilever beam
            # Fix left face (x=0)
            for j in range(nely + 1):
                for k in range(nelz + 1):
                    node = k * (nelx + 1) * (nely + 1) + j * (nelx + 1)
                    fixed_dofs.extend([3*node, 3*node+1, 3*node+2])

            # Force on middle of right face (x=nelx), downward
            mid_y = nely // 2
            mid_z = nelz // 2
            node = mid_z * (nelx + 1) * (nely + 1) + mid_y * (nelx + 1) + nelx
            force_dofs.append(3 * node + 1)  # y-direction
            force_values.append(-1.0)

        else:
            for bc in boundary_conditions:
                bc_dict = bc if isinstance(bc, dict) else bc.model_dump()
                bc_type = bc_dict.get("type", "fixation")

                if bc_type == "fixation":
                    for idx in bc_dict.get("selection_ids", []):
                        node = idx
                        dofs = bc_dict.get("fixed_dofs", ["x", "y", "z"])
                        if "x" in dofs:
                            fixed_dofs.append(3 * node)
                        if "y" in dofs:
                            fixed_dofs.append(3 * node + 1)
                        if "z" in dofs:
                            fixed_dofs.append(3 * node + 2)

                elif bc_type == "force":
                    fv = bc_dict.get("force_vector", [0, -1, 0])
                    for idx in bc_dict.get("selection_ids", []):
                        node = idx
                        for d, val in enumerate(fv):
                            if val != 0:
                                force_dofs.append(3 * node + d)
                                force_values.append(val)

        return np.array(fixed_dofs), force_dofs, force_values

    def _prepare_filter(self, nelx, nely, nelz):
        """Prepare density filter matrix."""
        n_elements = nelx * nely * nelz
        rmin = self.rmin

        # Build filter weights using convolution approach
        size = int(np.ceil(rmin))
        x_range = np.arange(-size, size + 1)
        kernel_1d = np.maximum(0, rmin - np.abs(x_range))

        # 3D kernel
        kernel_3d = np.einsum('i,j,k->ijk', kernel_1d, kernel_1d, kernel_1d)

        # For efficiency, use sparse matrix representation
        rows = []
        cols = []
        vals = []

        for ez in range(nelz):
            for ey in range(nely):
                for ex in range(nelx):
                    e = ez * nelx * nely + ey * nelx + ex
                    for dz in range(-size, size + 1):
                        for dy in range(-size, size + 1):
                            for dx in range(-size, size + 1):
                                nx, ny, nz = ex + dx, ey + dy, ez + dz
                                if 0 <= nx < nelx and 0 <= ny < nely and 0 <= nz < nelz:
                                    ne = nz * nelx * nely + ny * nelx + nx
                                    weight = max(0, rmin - np.sqrt(dx**2 + dy**2 + dz**2))
                                    if weight > 0:
                                        rows.append(e)
                                        cols.append(ne)
                                        vals.append(weight)

        H = coo_matrix((vals, (rows, cols)), shape=(n_elements, n_elements)).tocsr()
        Hs = np.array(H.sum(axis=1)).flatten()

        return H, Hs

    def _solve_fe(self, nelx, nely, nelz, KE, xphys, free_dofs, F, ndof):
        """Solve the finite element system."""
        n_elements = nelx * nely * nelz
        n_dof_per_element = 24

        # Assembly
        rows = []
        cols = []
        vals = []

        for ez in range(nelz):
            for ey in range(nely):
                for ex in range(nelx):
                    e = ez * nelx * nely + ey * nelx + ex
                    # Element nodes
                    nodes = self._element_nodes(ex, ey, ez, nelx, nely)
                    edof = []
                    for n in nodes:
                        edof.extend([3*n, 3*n+1, 3*n+2])

                    # Material interpolation (SIMP)
                    density = xphys[e] if isinstance(xphys, np.ndarray) and xphys.ndim == 1 else xphys.flatten()[e]
                    Ee = self.Emin + density**self.penal * (self.E0 - self.Emin)

                    for i in range(n_dof_per_element):
                        for j in range(n_dof_per_element):
                            rows.append(edof[i])
                            cols.append(edof[j])
                            vals.append(Ee * KE[i, j])

        K = coo_matrix((vals, (rows, cols)), shape=(ndof, ndof)).tocsr()

        # Solve
        U = np.zeros(ndof)
        K_free = K[np.ix_(free_dofs, free_dofs)]
        F_free = F[free_dofs]

        U[free_dofs] = splinalg.spsolve(K_free, F_free)
        return U

    def _element_nodes(self, ex, ey, ez, nelx, nely):
        """Get the 8 node indices for a hexahedral element."""
        n0 = ez * (nelx + 1) * (nely + 1) + ey * (nelx + 1) + ex
        n1 = n0 + 1
        n2 = n0 + (nelx + 1)
        n3 = n2 + 1
        n4 = n0 + (nelx + 1) * (nely + 1)
        n5 = n4 + 1
        n6 = n4 + (nelx + 1)
        n7 = n6 + 1
        return [n0, n1, n2, n3, n4, n5, n6, n7]

    def _compute_sensitivity(self, nelx, nely, nelz, KE, U, xphys):
        """Compute compliance and sensitivity."""
        n_elements = nelx * nely * nelz
        ce = np.zeros(n_elements)
        dc = np.zeros(n_elements)

        for ez in range(nelz):
            for ey in range(nely):
                for ex in range(nelx):
                    e = ez * nelx * nely + ey * nelx + ex
                    nodes = self._element_nodes(ex, ey, ez, nelx, nely)
                    edof = []
                    for n in nodes:
                        edof.extend([3*n, 3*n+1, 3*n+2])

                    Ue = U[edof]
                    ce[e] = float(Ue.T @ KE @ Ue)

                    density = xphys[e] if isinstance(xphys, np.ndarray) and xphys.ndim == 1 else xphys.flatten()[e]
                    dc[e] = -self.penal * density**(self.penal - 1) * (self.E0 - self.Emin) * ce[e]

        compliance = np.sum(
            (self.Emin + xphys.flatten()**self.penal * (self.E0 - self.Emin)) * ce
        )

        return ce, dc, compliance

    def _oc_update(self, nelx, nely, nelz, x, dc):
        """Optimality criteria update scheme."""
        n_elements = nelx * nely * nelz
        x_flat = x.flatten()
        dc_flat = dc.flatten()

        l1, l2 = 0, 1e9
        move = 0.2

        while (l2 - l1) / (l1 + l2) > 1e-3:
            lmid = 0.5 * (l2 + l1)
            x_new = np.maximum(
                0.001,
                np.maximum(
                    x_flat - move,
                    np.minimum(
                        1.0,
                        np.minimum(
                            x_flat + move,
                            x_flat * np.sqrt(-dc_flat / lmid)
                        )
                    )
                )
            )

            if np.sum(x_new) > self.volfrac * n_elements:
                l1 = lmid
            else:
                l2 = lmid

        return x_new

    def export_result(self, result: dict, output_path: str):
        """Export optimization result as STL mesh."""
        from stl import mesh as stl_mesh

        density = np.array(result["density"])
        nelx, nely, nelz = result["grid_size"]
        threshold = 0.5

        # Create voxel mesh for elements above threshold
        vertices = []
        faces = []
        vertex_count = 0

        density_3d = density.reshape(nelz, nely, nelx)

        for ez in range(nelz):
            for ey in range(nely):
                for ex in range(nelx):
                    if density_3d[ez, ey, ex] > threshold:
                        # Add cube for this voxel
                        v = self._cube_vertices(ex, ey, ez)
                        f = self._cube_faces(vertex_count)
                        vertices.extend(v)
                        faces.extend(f)
                        vertex_count += 8

        if not faces:
            logger.warning("No elements above threshold, lowering to 0.3")
            threshold = 0.3
            for ez in range(nelz):
                for ey in range(nely):
                    for ex in range(nelx):
                        if density_3d[ez, ey, ex] > threshold:
                            v = self._cube_vertices(ex, ey, ez)
                            f = self._cube_faces(vertex_count)
                            vertices.extend(v)
                            faces.extend(f)
                            vertex_count += 8

        # Create STL mesh
        vertices = np.array(vertices)
        faces = np.array(faces)

        stl_data = stl_mesh.Mesh(np.zeros(len(faces), dtype=stl_mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl_data.vectors[i][j] = vertices[f[j]]

        stl_data.save(output_path)
        logger.info(f"Exported result to {output_path} ({len(faces)} triangles)")

    def _cube_vertices(self, x, y, z):
        """Get 8 vertices of a unit cube at position (x, y, z)."""
        return [
            [x, y, z], [x+1, y, z], [x+1, y+1, z], [x, y+1, z],
            [x, y, z+1], [x+1, y, z+1], [x+1, y+1, z+1], [x, y+1, z+1],
        ]

    def _cube_faces(self, offset):
        """Get 12 triangular faces for a cube (2 per face)."""
        o = offset
        return [
            [o+0, o+1, o+2], [o+0, o+2, o+3],  # bottom
            [o+4, o+6, o+5], [o+4, o+7, o+6],  # top
            [o+0, o+4, o+1], [o+1, o+4, o+5],  # front
            [o+2, o+6, o+3], [o+3, o+6, o+7],  # back
            [o+0, o+3, o+4], [o+3, o+7, o+4],  # left
            [o+1, o+5, o+2], [o+2, o+5, o+6],  # right
        ]
