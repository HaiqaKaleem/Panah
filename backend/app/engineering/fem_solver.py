"""FEM Solver — Direct Stiffness Method for 2D/3D frames.

Implements real structural analysis:
- Element stiffness matrices (local + global)
- Coordinate transformations
- Assembly of global stiffness matrix
- Boundary condition application
- Solve for displacements and reactions
- Internal forces (axial, shear, moment) per element

References:
- Matrix Structural Analysis, McGuire, Gallagher & Ziemian
- ASCE 7 for load combinations
- AISC Manual for member properties
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Data Structures ──────────────────────────────────────────────────


class SupportType(str, Enum):
    FREE = "free"
    PINNED = "pinned"
    FIXED = "fixed"
    ROLLER_X = "roller_x"
    ROLLER_Y = "roller_y"
    ROLLER_Z = "roller_z"


class LoadType(str, Enum):
    POINT = "point"
    DISTRIBUTED = "distributed"
    MOMENT = "moment"


@dataclass
class Node:
    """A structural node (joint) with coordinates and support conditions."""
    id: int
    x: float
    y: float
    z: float = 0.0
    support: SupportType = SupportType.FREE

    # Degrees of freedom: [ux, uy, uz, rx, ry, rz]
    # For 2D: only ux, uy, rz are active
    def is_3d(self) -> bool:
        return self.z != 0.0

    def restrained_dofs(self, is_3d: bool = False) -> list[int]:
        """Return indices of restrained DOFs for this node."""
        base = self.id * (6 if is_3d else 3)
        if self.support == SupportType.FREE:
            return []
        elif self.support == SupportType.PINNED:
            return [base, base + 1] if not is_3d else [base, base + 1, base + 2]
        elif self.support == SupportType.FIXED:
            n = 6 if is_3d else 3
            return list(range(base, base + n))
        elif self.support == SupportType.ROLLER_X:
            return [base] if not is_3d else [base]
        elif self.support == SupportType.ROLLER_Y:
            return [base + 1] if not is_3d else [base + 1]
        elif self.support == SupportType.ROLLER_Z:
            return [base + 2] if is_3d else []
        return []


@dataclass
class Material:
    """Material properties."""
    name: str
    E: float  # Young's modulus (Pa or N/mm²)
    G: float = 0.0  # Shear modulus (auto-calculated if 0)
    density: float = 7850.0  # kg/m³
    yield_strength: float = 250e6  # Pa

    def __post_init__(self):
        if self.G == 0:
            self.G = self.E / (2 * (1 + 0.3))  # Assume ν = 0.3


@dataclass
class Section:
    """Cross-section properties."""
    name: str
    A: float  # Cross-sectional area (m²)
    Ix: float  # Second moment of area about x-axis (m⁴)
    Iy: float = 0.0  # Second moment of area about y-axis (m⁴)
    J: float = 0.0  # Torsion constant (m⁴)
    Zx: float = 0.0  # Elastic section modulus (m³)
    Zy: float = 0.0  # Elastic section modulus (m³)
    Sx: float = 0.0  # Plastic section modulus (m³)
    depth: float = 0.0  # Section depth (m)
    width: float = 0.0  # Section width (m)
    weight_per_length: float = 0.0  # kg/m

    def __post_init__(self):
        if self.J == 0 and self.Ix > 0:
            self.J = self.Ix * 0.8  # Approximate for open sections
        if self.Zx == 0 and self.Ix > 0 and self.depth > 0:
            self.Zx = 2 * self.Ix / self.depth


@dataclass
class PointLoad:
    """A point load applied at a specific location along an element."""
    node_id: int
    fx: float = 0.0  # Force in x (N)
    fy: float = 0.0  # Force in y (N)
    fz: float = 0.0  # Force in z (N) — 3D only
    mx: float = 0.0  # Moment about x — 3D only
    my: float = 0.0  # Moment about y — 3D only
    mz: float = 0.0  # Moment about z (2D: out-of-plane)


@dataclass
class DistributedLoad:
    """A distributed load along an element (local coordinates)."""
    element_id: int
    wx: float = 0.0  # Load per unit length, local x
    wy: float = 0.0  # Load per unit length, local y (perpendicular)


@dataclass
class Element:
    """A beam/column element connecting two nodes."""
    id: int
    node_i: int  # Start node ID
    node_j: int  # End node ID
    material: Material
    section: Section
    # Optional releases (true = pinned at that end for that DOF)
    release_i: bool = False  # Moment release at start
    release_j: bool = False  # Moment release at end


@dataclass
class AnalysisResult:
    """Complete result of a structural analysis."""
    # Displacements per node: [ux, uy, uz, rx, ry, rz]
    displacements: dict[int, list[float]]
    # Reactions per restrained node: [Fx, Fy, Fz, Mx, My, Mz]
    reactions: dict[int, list[float]]
    # Internal forces per element
    element_forces: dict[int, "ElementForces"]
    # Max values for summary
    max_displacement: float = 0.0
    max_axial_force: float = 0.0
    max_shear_force: float = 0.0
    max_bending_moment: float = 0.0
    # Status
    success: bool = True
    message: str = "Analysis completed successfully"
    # Convergence info
    iterations: int = 0


@dataclass
class ElementForces:
    """Internal forces for a single element (end forces in local coordinates)."""
    element_id: int
    # Forces at start (local): [N, Vy, Vz, T, My, Mz]
    ni: float = 0.0  # Axial
    viy: float = 0.0  # Shear y
    viz: float = 0.0  # Shear z
    ti: float = 0.0  # Torsion
    miy: float = 0.0  # Moment y
    miz: float = 0.0  # Moment z
    # Forces at end (local)
    nj: float = 0.0
    vjy: float = 0.0
    vjz: float = 0.0
    tj: float = 0.0
    mjy: float = 0.0
    mjz: float = 0.0
    # Maximum values along element
    max_moment: float = 0.0
    max_shear: float = 0.0
    max_deflection: float = 0.0
    # Diagram data (stations along element length)
    moment_diagram: list[tuple[float, float]] = field(default_factory=list)
    shear_diagram: list[tuple[float, float]] = field(default_factory=list)
    deflection_diagram: list[tuple[float, float]] = field(default_factory=list)


# ── FEM Solver ───────────────────────────────────────────────────────


class FEMSolver2D:
    """2D Frame Analysis using Direct Stiffness Method.

    DOFs per node: [ux, uy, rz]  (3 DOFs)
    Element stiffness: 6x6 in local coords → 6x6 in global coords
    """

    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.elements: dict[int, Element] = {}
        self.point_loads: list[PointLoad] = []
        self.distributed_loads: list[DistributedLoad] = []
        self.n_dofs: int = 0

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_element(self, element: Element) -> None:
        self.elements[element.id] = element

    def add_point_load(self, load: PointLoad) -> None:
        self.point_loads.append(load)

    def add_distributed_load(self, load: DistributedLoad) -> None:
        self.distributed_loads.append(load)

    def _element_length(self, elem: Element) -> float:
        ni = self.nodes[elem.node_i]
        nj = self.nodes[elem.node_j]
        dx = nj.x - ni.x
        dy = nj.y - ni.y
        return math.sqrt(dx * dx + dy * dy)

    def _element_rotation(self, elem: Element) -> float:
        ni = self.nodes[elem.node_i]
        nj = self.nodes[elem.node_j]
        L = self._element_length(elem)
        cos_a = (nj.x - ni.x) / L
        sin_a = (nj.y - ni.y) / L
        return cos_a, sin_a

    def _local_stiffness(self, elem: Element) -> list[list[float]]:
        """Compute 6x6 element stiffness matrix in local coordinates."""
        L = self._element_length(elem)
        E = elem.material.E
        A = elem.section.A
        I = elem.section.Ix

        # Simplified: all DOFs active (no releases)
        EA_L = E * A / L
        EI_L3 = E * I / (L * L * L)
        EI_L = E * I / L
        EI_L2 = E * I / (L * L)

        # 6x6 local stiffness matrix
        # DOFs: [u1, v1, θ1, u2, v2, θ2]
        K = [
            [ EA_L,    0,        0,       -EA_L,    0,        0      ],
            [ 0,       12*EI_L3, 6*EI_L2, 0,      -12*EI_L3, 6*EI_L2],
            [ 0,       6*EI_L2,  4*EI_L,  0,      -6*EI_L2,  2*EI_L ],
            [-EA_L,    0,        0,        EA_L,    0,        0      ],
            [ 0,      -12*EI_L3,-6*EI_L2, 0,       12*EI_L3,-6*EI_L2],
            [ 0,       6*EI_L2,  2*EI_L,  0,      -6*EI_L2,  4*EI_L ],
        ]

        # Apply moment releases (pinned ends)
        if elem.release_i or elem.release_j:
            K = self._apply_releases(K, elem.release_i, elem.release_j)

        return K

    def _apply_releases(
        self, K: list[list[float]], release_i: bool, release_j: bool
    ) -> list[list[float]]:
        """Apply moment releases using static condensation."""
        # For simplicity, zero out the moment DOFs at released ends
        # and redistribute (simplified approach)
        K_mod = [row[:] for row in K]
        if release_i:
            # Pin at start: zero moment at node i (DOF index 2)
            for i in range(6):
                K_mod[2][i] = 0.0
                K_mod[i][2] = 0.0
            K_mod[2][2] = 1.0  # Prevent singularity
        if release_j:
            # Pin at end: zero moment at node j (DOF index 5)
            for i in range(6):
                K_mod[5][i] = 0.0
                K_mod[i][5] = 0.0
            K_mod[5][5] = 1.0
        return K_mod

    def _transformation_matrix(self, elem: Element) -> list[list[float]]:
        """6x6 transformation matrix from local to global coordinates."""
        cos_a, sin_a = self._element_rotation(elem)

        T = [
            [cos_a,  sin_a, 0, 0,      0,      0],
            [-sin_a, cos_a, 0, 0,      0,      0],
            [0,      0,     1, 0,      0,      0],
            [0,      0,     0, cos_a,  sin_a,  0],
            [0,      0,     0,-sin_a,  cos_a,  0],
            [0,      0,     0, 0,      0,      1],
        ]
        return T

    def _assemble_global(self) -> tuple[list[list[float]], list[float]]:
        """Assemble global stiffness matrix and load vector."""
        self.n_dofs = len(self.nodes) * 3  # 3 DOFs per node (2D)
        K_global = [[0.0] * self.n_dofs for _ in range(self.n_dofs)]
        F_global = [0.0] * self.n_dofs

        # Assemble element contributions
        for elem in self.elements.values():
            K_local = self._local_stiffness(elem)
            T = self._transformation_matrix(elem)

            # K_global_element = T^T * K_local * T
            KT = self._mat_mul_transpose(T, K_local)
            K_elem = self._mat_mul(KT, T)

            # Get DOF indices
            ni = self.nodes[elem.node_i]
            nj = self.nodes[elem.node_j]
            dofs_i = [ni.id * 3, ni.id * 3 + 1, ni.id * 3 + 2]
            dofs_j = [nj.id * 3, nj.id * 3 + 1, nj.id * 3 + 2]
            dofs = dofs_i + dofs_j

            # Assemble
            for i_local in range(6):
                for j_local in range(6):
                    K_global[dofs[i_local]][dofs[j_local]] += K_elem[i_local][j_local]

        # Apply point loads
        for load in self.point_loads:
            if load.node_id in self.nodes:
                node = self.nodes[load.node_id]
                F_global[node.id * 3] += load.fx
                F_global[node.id * 3 + 1] += load.fy
                F_global[node.id * 3 + 2] += load.mz

        # Apply distributed loads as equivalent nodal loads
        for dload in self.distributed_loads:
            if dload.element_id in self.elements:
                elem = self.elements[dload.element_id]
                L = self._element_length(elem)
                ni = self.nodes[elem.node_i]
                nj = self.nodes[elem.node_j]
                cos_a, sin_a = self._element_rotation(elem)

                # Fixed-end forces for UDL in local coords
                # Fy_end = wL/2, M_end = wL²/12
                wy_fixed = dload.wy * L / 2
                mz_fixed_i = dload.wy * L * L / 12
                mz_fixed_j = -dload.wy * L * L / 12

                # Transform to global
                fx_i = -wy_fixed * sin_a
                fy_i = wy_fixed * cos_a
                mz_i = mz_fixed_i
                fx_j = -wy_fixed * sin_a
                fy_j = wy_fixed * cos_a
                mz_j = mz_fixed_j

                # Note: for consistent nodal loads, we SUBTRACT the fixed-end forces
                # (equivalent nodal load = -fixed-end force)
                F_global[ni.id * 3] -= fx_i
                F_global[ni.id * 3 + 1] -= fy_i
                F_global[ni.id * 3 + 2] -= mz_i
                F_global[nj.id * 3] -= fx_j
                F_global[nj.id * 3 + 1] -= fy_j
                F_global[nj.id * 3 + 2] -= mz_j

        return K_global, F_global

    def solve(self) -> AnalysisResult:
        """Run the full structural analysis."""
        try:
            K_global, F_global = self._assemble_global()

            # Identify restrained and free DOFs
            is_3d = False
            restrained = []
            for node in self.nodes.values():
                restrained.extend(node.restrained_dofs(is_3d))
            restrained = sorted(set(restrained))
            free = [i for i in range(self.n_dofs) if i not in restrained]

            if not free:
                return AnalysisResult(
                    displacements={}, reactions={}, element_forces={},
                    success=False, message="No free DOFs — structure is fully restrained"
                )

            # Extract submatrices
            n_free = len(free)
            n_rest = len(restrained)

            K_ff = [[K_global[i][j] for j in free] for i in free]
            F_f = [F_global[i] for i in free]

            # Solve K_ff * U_f = F_f using Gaussian elimination
            U_f = self._gaussian_elimination(K_ff, F_f)

            if U_f is None:
                return AnalysisResult(
                    displacements={}, reactions={}, element_forces={},
                    success=False, message="Singular stiffness matrix — structure is unstable"
                )

            # Full displacement vector
            U = [0.0] * self.n_dofs
            for idx, dof in enumerate(free):
                U[dof] = U_f[idx]

            # Compute reactions: R = K * U - F
            R = [0.0] * self.n_dofs
            for i in restrained:
                for j in range(self.n_dofs):
                    R[i] += K_global[i][j] * U[j]
                R[i] -= F_global[i]

            # Extract node displacements and reactions
            displacements = {}
            reactions = {}
            for node in self.nodes.values():
                base = node.id * 3
                displacements[node.id] = [U[base], U[base + 1], U[base + 2]]
                if node.support != SupportType.FREE:
                    reactions[node.id] = [R[base], R[base + 1], R[base + 2]]

            # Compute element forces
            element_forces = self._compute_element_forces(U)

            # Summary statistics
            max_disp = 0.0
            for d in displacements.values():
                mag = math.sqrt(d[0] ** 2 + d[1] ** 2)
                max_disp = max(max_disp, mag)

            max_axial = 0.0
            max_shear = 0.0
            max_moment = 0.0
            for ef in element_forces.values():
                max_axial = max(max_axial, abs(ef.ni), abs(ef.nj))
                max_shear = max(max_shear, abs(ef.viy), abs(ef.vjy))
                max_moment = max(max_moment, abs(ef.miz), abs(ef.mjz))

            return AnalysisResult(
                displacements=displacements,
                reactions=reactions,
                element_forces=element_forces,
                max_displacement=max_disp,
                max_axial_force=max_axial,
                max_shear_force=max_shear,
                max_bending_moment=max_moment,
                success=True,
            )

        except Exception as e:
            return AnalysisResult(
                displacements={}, reactions={}, element_forces={},
                success=False, message=f"Analysis failed: {str(e)}"
            )

    def _compute_element_forces(self, U: list[float]) -> dict[int, ElementForces]:
        """Compute internal forces for each element."""
        results = {}
        n_stations = 21  # Points along element for diagrams

        for elem in self.elements.values():
            L = self._element_length(elem)
            ni = self.nodes[elem.node_i]
            nj = self.nodes[elem.node_j]

            # Get element displacements in global coords
            dofs_i = [ni.id * 3, ni.id * 3 + 1, ni.id * 3 + 2]
            dofs_j = [nj.id * 3, nj.id * 3 + 1, nj.id * 3 + 2]
            u_global = [U[d] for d in dofs_i + dofs_j]

            # Transform to local
            T = self._transformation_matrix(elem)
            u_local = self._mat_vec(T, u_global)

            # Local element forces
            K_local = self._local_stiffness(elem)
            f_local = self._mat_vec(K_local, u_local)

            # Find distributed loads on this element
            w = 0.0
            for dload in self.distributed_loads:
                if dload.element_id == elem.id:
                    w = dload.wy

            # Generate diagrams
            moment_diag = []
            shear_diag = []
            deflection_diag = []

            E = elem.material.E
            I = elem.section.Ix
            EI = E * I

            max_m = 0.0
            max_v = 0.0
            max_d = 0.0

            for i in range(n_stations):
                x = L * i / (n_stations - 1)
                xi = x / L

                # Shear force: V(x) = V_i - w*x (for UDL)
                V = f_local[1] - w * x
                shear_diag.append((x, V))
                max_v = max(max_v, abs(V))

                # Bending moment: M(x) = M_i + V_i*x - w*x²/2
                M = f_local[2] + f_local[1] * x - w * x * x / 2
                moment_diag.append((x, M))
                max_m = max(max_m, abs(M))

                # Deflection (approximate using beam theory)
                if EI > 0:
                    # v(x) = v_i*(1-x/L) + v_j*(x/L) + (x/L)*(1-x/L) *
                    #        [M_i*L*(1-x/L)/6 + M_j*L*(x/L)/6]
                    v_i = u_local[1]
                    v_j = u_local[4]
                    theta_i = u_local[2]
                    theta_j = u_local[5]

                    # Hermite interpolation
                    N1 = 1 - 3 * xi ** 2 + 2 * xi ** 3
                    N2 = L * (xi - 2 * xi ** 2 + xi ** 3)
                    N3 = 3 * xi ** 2 - 2 * xi ** 3
                    N4 = L * (-xi ** 2 + xi ** 3)

                    # Plus particular solution for UDL
                    v_udl = w * L ** 4 / (24 * EI) * (
                        xi - 2 * xi ** 3 + xi ** 4
                    )

                    delta = N1 * v_i + N2 * theta_i + N3 * v_j + N4 * theta_j + v_udl
                    deflection_diag.append((x, delta))
                    max_d = max(max_d, abs(delta))
                else:
                    deflection_diag.append((x, 0.0))

            ef = ElementForces(
                element_id=elem.id,
                ni=f_local[0], viy=f_local[1], miz=f_local[2],
                nj=f_local[3], vjy=f_local[4], mjz=f_local[5],
                max_moment=max_m,
                max_shear=max_v,
                max_deflection=max_d,
                moment_diagram=moment_diag,
                shear_diagram=shear_diag,
                deflection_diagram=deflection_diag,
            )
            results[elem.id] = ef

        return results

    def _gaussian_elimination(
        self, A: list[list[float]], b: list[float]
    ) -> list[float] | None:
        """Solve Ax = b using Gaussian elimination with partial pivoting."""
        n = len(b)
        # Augmented matrix
        M = [A[i][:] + [b[i]] for i in range(n)]

        for col in range(n):
            # Partial pivoting
            max_row = col
            max_val = abs(M[col][col])
            for row in range(col + 1, n):
                if abs(M[row][col]) > max_val:
                    max_val = abs(M[row][col])
                    max_row = row
            M[col], M[max_row] = M[max_row], M[col]

            if abs(M[col][col]) < 1e-12:
                return None  # Singular

            # Eliminate
            for row in range(col + 1, n):
                factor = M[row][col] / M[col][col]
                for j in range(col, n + 1):
                    M[row][j] -= factor * M[col][j]

        # Back substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = M[i][n]
            for j in range(i + 1, n):
                x[i] -= M[i][j] * x[j]
            x[i] /= M[i][i]

        return x

    # ── Matrix Utilities ─────────────────────────────────────────────

    @staticmethod
    def _mat_mul(A: list[list[float]], B: list[list[float]]) -> list[list[float]]:
        n, m, p = len(A), len(B), len(B[0])
        C = [[0.0] * p for _ in range(n)]
        for i in range(n):
            for j in range(p):
                for k in range(m):
                    C[i][j] += A[i][k] * B[k][j]
        return C

    @staticmethod
    def _mat_mul_transpose(
        A: list[list[float]], B: list[list[float]]
    ) -> list[list[float]]:
        """Compute A^T * B."""
        n, m = len(A), len(A[0])
        p = len(B[0])
        C = [[0.0] * p for _ in range(m)]
        for i in range(m):
            for j in range(p):
                for k in range(n):
                    C[i][j] += A[k][i] * B[k][j]
        return C

    @staticmethod
    def _mat_vec(A: list[list[float]], v: list[float]) -> list[float]:
        n, m = len(A), len(v)
        result = [0.0] * n
        for i in range(n):
            for j in range(m):
                result[i] += A[i][j] * v[j]
        return result


# ── Convenience Functions ────────────────────────────────────────────


def analyze_simple_beam(
    L: float,
    E: float,
    I: float,
    A: float,
    loads: list[dict],
    n_elements: int = 10,
) -> AnalysisResult:
    """Analyze a simply supported beam with given loads.

    Args:
        L: Span length (m)
        E: Young's modulus (Pa)
        I: Second moment of area (m⁴)
        A: Cross-sectional area (m²)
        loads: List of load dicts with keys:
            - type: 'point' | 'distributed'
            - position: fraction of span (0-1) for point loads
            - magnitude: force (N) or load/length (N/m)
            - direction: 'vertical' (default) or 'horizontal'
        n_elements: Number of elements for mesh

    Returns:
        AnalysisResult with displacements, reactions, element forces
    """
    mat = Material(name="Steel", E=E)
    sec = Section(name="Beam", A=A, Ix=I)
    solver = FEMSolver2D()

    # Nodes along beam
    for i in range(n_elements + 1):
        x = L * i / n_elements
        support = SupportType.FREE
        if i == 0:
            support = SupportType.PINNED
        elif i == n_elements:
            support = SupportType.ROLLER_Y
        solver.add_node(Node(id=i, x=x, y=0.0, support=support))

    # Elements
    for i in range(n_elements):
        solver.add_element(Element(
            id=i, node_i=i, node_j=i + 1,
            material=mat, section=sec,
        ))

    # Apply loads
    load_id = 0
    for load in loads:
        if load["type"] == "point":
            pos = load.get("position", 0.5)
            mag = load["magnitude"]
            node_x = L * pos
            # Find nearest node
            nearest = min(range(n_elements + 1),
                          key=lambda i: abs(L * i / n_elements - node_x))
            solver.add_point_load(PointLoad(
                node_id=nearest,
                fy=-mag if load.get("direction", "vertical") == "vertical" else 0,
                fx=-mag if load.get("direction", "vertical") == "horizontal" else 0,
            ))
        elif load["type"] == "distributed":
            mag = load["magnitude"]
            # Apply to all elements
            for elem_id in range(n_elements):
                solver.add_distributed_load(DistributedLoad(
                    element_id=elem_id, wy=-mag,
                ))

    return solver.solve()


def analyze_portal_frame(
    width: float,
    height: float,
    E: float,
    I_col: float,
    I_beam: float,
    A_col: float,
    A_beam: float,
    loads: list[dict],
) -> AnalysisResult:
    """Analyze a simple portal frame (2 columns + 1 beam).

    Args:
        width: Frame width (m)
        height: Column height (m)
        E: Young's modulus (Pa)
        I_col: Column second moment of area (m⁴)
        I_beam: Beam second moment of area (m⁴)
        A_col: Column area (m²)
        A_beam: Beam area (m²)
        loads: List of load dicts with keys:
            - type: 'point' | 'distributed'
            - position: fraction along beam (0-1)
            - magnitude: force (N) or load/length (N/m)

    Returns:
        AnalysisResult
    """
    mat = Material(name="Steel", E=E)
    sec_col = Section(name="Column", A=A_col, Ix=I_col)
    sec_beam = Section(name="Beam", A=A_beam, Ix=I_beam)

    solver = FEMSolver2D()

    # Nodes: 0=left base, 1=left top, 2=right top, 3=right base
    solver.add_node(Node(id=0, x=0, y=0, support=SupportType.FIXED))
    solver.add_node(Node(id=1, x=0, y=height))
    solver.add_node(Node(id=2, x=width, y=height))
    solver.add_node(Node(id=3, x=width, y=0, support=SupportType.FIXED))

    # Elements
    solver.add_element(Element(id=0, node_i=0, node_j=1, material=mat, section=sec_col))
    solver.add_element(Element(id=1, node_i=1, node_j=2, material=mat, section=sec_beam))
    solver.add_element(Element(id=2, node_i=2, node_j=3, material=mat, section=sec_col))

    # Apply loads to beam (element 1)
    for load in loads:
        if load["type"] == "distributed":
            solver.add_distributed_load(DistributedLoad(
                element_id=1, wy=-load["magnitude"],
            ))
        elif load["type"] == "point":
            pos = load.get("position", 0.5)
            node_x = width * pos
            solver.add_point_load(PointLoad(
                node_id=1 if pos < 0.5 else 2,
                fy=-load["magnitude"],
            ))

    return solver.solve()
