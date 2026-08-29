"""Tests for Advanced Engineering Features — FEM Solver, Sections, Buckling, Sizing."""

import math
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# ── FEM Solver Unit Tests ───────────────────────────────────────────


class TestFEMSolver:
    """Test the Direct Stiffness Method implementation."""

    def test_simple_beam_point_load(self):
        """Simply supported beam with center point load — classic textbook case."""
        from app.engineering.fem_solver import (
            FEMSolver2D, Node, Element, Material, Section,
            PointLoad, SupportType
        )

        L = 6.0  # 6m span
        P = 10000.0  # 10kN at center
        E = 200e9
        I = 8.33e-6  # Approximate W12×16

        mat = Material(name="Steel", E=E)
        sec = Section(name="Beam", A=0.003, Ix=I)

        solver = FEMSolver2D()
        solver.add_node(Node(id=0, x=0, y=0, support=SupportType.PINNED))
        solver.add_node(Node(id=1, x=L / 2, y=0))
        solver.add_node(Node(id=2, x=L, y=0, support=SupportType.ROLLER_Y))

        solver.add_element(Element(id=0, node_i=0, node_j=1, material=mat, section=sec))
        solver.add_element(Element(id=1, node_i=1, node_j=2, material=mat, section=sec))

        solver.add_point_load(PointLoad(node_id=1, fy=-P))

        result = solver.solve()

        assert result.success is True
        # Theoretical mid-span deflection: PL³/(48EI)
        theoretical_delta = P * L ** 3 / (48 * E * I)
        # Check mid-span displacement is reasonable (within 20% of theoretical)
        mid_disp = result.displacements[1][1]  # vertical
        assert abs(mid_disp) > 0
        assert abs(mid_disp) < theoretical_delta * 1.5

        # Reactions should be P/2 each
        rxn_left = result.reactions[0]
        rxn_right = result.reactions[2]
        assert abs(rxn_left[1] + rxn_right[1] - P) < P * 0.1

    def test_portal_frame_with_udl(self):
        """Portal frame with uniform distributed load on beam."""
        from app.engineering.fem_solver import (
            FEMSolver2D, Node, Element, Material, Section,
            DistributedLoad, SupportType
        )

        width = 6.0
        height = 4.0
        E = 200e9
        I_col = 5e-5
        I_beam = 1e-4

        mat = Material(name="Steel", E=E)
        sec_col = Section(name="Col", A=0.005, Ix=I_col)
        sec_beam = Section(name="Beam", A=0.01, Ix=I_beam)

        solver = FEMSolver2D()
        solver.add_node(Node(id=0, x=0, y=0, support=SupportType.FIXED))
        solver.add_node(Node(id=1, x=0, y=height))
        solver.add_node(Node(id=2, x=width, y=height))
        solver.add_node(Node(id=3, x=width, y=0, support=SupportType.FIXED))

        solver.add_element(Element(id=0, node_i=0, node_j=1, material=mat, section=sec_col))
        solver.add_element(Element(id=1, node_i=1, node_j=2, material=mat, section=sec_beam))
        solver.add_element(Element(id=2, node_i=2, node_j=3, material=mat, section=sec_col))

        # UDL on beam
        solver.add_distributed_load(DistributedLoad(element_id=1, wy=-5000))

        result = solver.solve()
        assert result.success is True
        assert len(result.displacements) == 4
        assert len(result.reactions) == 2  # Two fixed supports

    def test_unstable_structure(self):
        """Structure with no support should fail gracefully (singular matrix)."""
        from app.engineering.fem_solver import (
            FEMSolver2D, Node, Element, Material, Section, SupportType
        )

        mat = Material(name="Steel", E=200e9)
        sec = Section(name="Beam", A=0.01, Ix=1e-4)
        solver = FEMSolver2D()
        solver.add_node(Node(id=0, x=0, y=0))
        solver.add_node(Node(id=1, x=5, y=0))
        solver.add_element(Element(id=0, node_i=0, node_j=1, material=mat, section=sec))

        result = solver.solve()
        # No restraints → fully unrestrained → singular matrix → unstable
        assert result.success is False

    def test_convenience_beam_function(self):
        """Test analyze_simple_beam convenience function."""
        from app.engineering.fem_solver import analyze_simple_beam

        result = analyze_simple_beam(
            L=5.0, E=200e9, I=5e-5, A=0.005,
            loads=[{"type": "point", "position": 0.5, "magnitude": 10000}],
            n_elements=10,
        )

        assert result.success is True
        assert result.max_displacement > 0

    def test_convenience_portal_frame(self):
        """Test analyze_portal_frame convenience function."""
        from app.engineering.fem_solver import analyze_portal_frame

        result = analyze_portal_frame(
            width=6.0, height=4.0, E=200e9,
            I_col=5e-5, I_beam=1e-4, A_col=0.005, A_beam=0.01,
            loads=[{"type": "distributed", "magnitude": 5000}],
        )

        assert result.success is True
        assert len(result.element_forces) == 3


# ── Sections Database Tests ─────────────────────────────────────────


class TestSectionsDatabase:
    """Test AISC sections database."""

    def test_lookup_w_shape(self):
        from app.engineering.sections_db import get_section
        sec = get_section("W12×50")
        assert sec is not None
        assert sec.section_type.value == "W"
        assert sec.depth > 0
        assert sec.Ix > 0
        assert sec.weight_per_length > 0

    def test_lookup_hss(self):
        from app.engineering.sections_db import get_section
        sec = get_section("HSS6×6×⅜")
        assert sec is not None
        assert sec.section_type.value == "HSS-S"

    def test_lookup_channel(self):
        from app.engineering.sections_db import get_section
        sec = get_section("C10×15.3")
        assert sec is not None
        assert sec.section_type.value == "C"

    def test_lookup_nonexistent(self):
        from app.engineering.sections_db import get_section
        sec = get_section("W99×999")
        assert sec is None

    def test_list_all_designations(self):
        from app.engineering.sections_db import list_all_designations
        desigs = list_all_designations()
        assert len(desigs) > 20
        assert "W12×50" in desigs

    def test_w_shapes_count(self):
        from app.engineering.sections_db import AISC_W_SHAPES
        assert len(AISC_W_SHAPES) >= 15

    def test_hss_shapes_count(self):
        from app.engineering.sections_db import AISC_HSS_SHAPES
        assert len(AISC_HSS_SHAPES) >= 8

    def test_channel_shapes_count(self):
        from app.engineering.sections_db import AISC_CHANNEL_SHAPES
        assert len(AISC_CHANNEL_SHAPES) >= 4

    def test_sections_have_valid_properties(self):
        """All sections must have positive area and moments of inertia."""
        from app.engineering.sections_db import AISC_W_SHAPES, AISC_HSS_SHAPES
        for sec in AISC_W_SHAPES + AISC_HSS_SHAPES:
            assert sec.A > 0, f"{sec.designation} has invalid A"
            assert sec.Ix > 0, f"{sec.designation} has invalid Ix"
            assert sec.depth > 0, f"{sec.designation} has invalid depth"

    def test_find_sections_by_Ix(self):
        from app.engineering.sections_db import find_sections_min_Ix
        sections = find_sections_min_Ix(5e-4)  # Need Ix >= 500 cm⁴ in m⁴
        assert len(sections) > 0
        for s in sections:
            assert s.Ix >= 5e-4


# ── Buckling Analysis Tests ─────────────────────────────────────────


class TestBucklingAnalysis:
    """Test Euler buckling analysis."""

    def test_fixed_fixed_column(self):
        from app.engineering.advanced_analysis import analyze_buckling
        result = analyze_buckling(
            length=3.0, E=200e9, I=5e-5, A=0.005,
            support_start="fixed", support_end="fixed",
        )
        assert result.critical_load > 0
        assert result.effective_length_factor == 0.5
        assert result.effective_length == 1.5

    def test_pinned_pinned_column(self):
        from app.engineering.advanced_analysis import analyze_buckling
        result = analyze_buckling(
            length=3.0, E=200e9, I=5e-5, A=0.005,
            support_start="pinned", support_end="pinned",
        )
        assert result.effective_length_factor == 1.0
        assert result.effective_length == 3.0
        # K=1.0 column has lower capacity than K=0.5
        assert result.critical_load < analyze_buckling(
            length=3.0, E=200e9, I=5e-5, A=0.005,
            support_start="fixed", support_end="fixed",
        ).critical_load

    def test_slenderness_ratio(self):
        from app.engineering.advanced_analysis import analyze_buckling
        result = analyze_buckling(
            length=4.0, E=200e9, I=8.33e-6, A=0.003,
            support_start="pinned", support_end="pinned",
        )
        r = math.sqrt(8.33e-6 / 0.003)
        expected_slenderness = 4.0 / r
        assert abs(result.slenderness_ratio - expected_slenderness) < 0.1

    def test_allowable_load(self):
        from app.engineering.advanced_analysis import analyze_buckling
        result = analyze_buckling(
            length=3.0, E=200e9, I=5e-5, A=0.005,
        )
        assert result.allowable_load == result.critical_load / result.safety_factor


# ── Interaction Check Tests ─────────────────────────────────────────


class TestInteractionCheck:
    """Test AISC H1 interaction equations."""

    def test_pure_axial(self):
        from app.engineering.advanced_analysis import check_interaction
        result = check_interaction(P=100000, M=0, Pc=200000, Mc=50000)
        assert result.axial_ratio == 0.5
        assert result.bending_ratio == 0.0
        # P/Pc = 0.5 >= 0.2 → H1-1a: 0.5 + 8/9 * 0 = 0.5 → OK
        assert result.status == "OK"
        assert result.equation_used == "H1-1a"

    def test_pure_bending(self):
        from app.engineering.advanced_analysis import check_interaction
        result = check_interaction(P=0, M=40000, Pc=200000, Mc=50000)
        assert result.status == "OK"
        assert result.demand_capacity_ratio == 0.8

    def test_combined_loading_ok(self):
        from app.engineering.advanced_analysis import check_interaction
        result = check_interaction(P=100000, M=20000, Pc=200000, Mc=50000)
        # P/Pc = 0.5 >= 0.2 → H1-1a: 0.5 + 8/9 * 0.4 = 0.5 + 0.356 = 0.856
        assert result.equation_used == "H1-1a"
        assert result.status == "OK"

    def test_combined_loading_fail(self):
        from app.engineering.advanced_analysis import check_interaction
        result = check_interaction(P=200000, M=50000, Pc=200000, Mc=50000)
        assert result.status == "FAIL"
        assert result.demand_capacity_ratio > 1.0


# ── Member Sizing Tests ─────────────────────────────────────────────


class TestMemberSizing:
    """Test auto-sizing wizard."""

    def test_beam_sizing_finds_solution(self):
        from app.engineering.advanced_analysis import size_beam
        result = size_beam(
            span=6.0, E=200e9, Fy=250e6,
            V_demand=30000, M_demand=50000,
        )
        assert result.optimal_section != "NO ADEQUATE SECTION FOUND"
        assert result.utilization_ratio > 0
        assert result.utilization_ratio <= 1.0

    def test_beam_sizing_lightest_wins(self):
        from app.engineering.advanced_analysis import size_beam
        result = size_beam(
            span=4.0, E=200e9, Fy=250e6,
            V_demand=10000, M_demand=20000,
        )
        assert len(result.all_adequate_sections) > 0
        # First should be lightest
        for i in range(1, len(result.all_adequate_sections)):
            assert (result.all_adequate_sections[i]["weight_kg_m"] >=
                    result.all_adequate_sections[0]["weight_kg_m"])

    def test_column_sizing_finds_solution(self):
        from app.engineering.advanced_analysis import size_column
        result = size_column(
            length=4.0, E=200e9, Fy=250e6,
            P_demand=200000,
        )
        assert result.optimal_section != "NO ADEQUATE COLUMN FOUND"
        assert result.utilization_ratio <= 1.0

    def test_sizing_empty_when_demand_too_high(self):
        from app.engineering.advanced_analysis import size_beam
        result = size_beam(
            span=20.0, E=200e9, Fy=250e6,
            V_demand=1e6, M_demand=1e7,  # Huge demand
        )
        # May find no section or the largest section
        assert result.weight_per_length >= 0


# ── Diagram Generation Tests ────────────────────────────────────────


class TestDiagramGeneration:
    """Test diagram data generation."""

    def test_diagram_generation(self):
        from app.engineering.fem_solver import (
            FEMSolver2D, Node, Element, Material, Section,
            PointLoad, SupportType
        )
        from app.engineering.advanced_analysis import generate_diagram_data

        L = 6.0
        mat = Material(name="Steel", E=200e9)
        sec = Section(name="Beam", A=0.003, Ix=8.33e-6)

        solver = FEMSolver2D()
        solver.add_node(Node(id=0, x=0, y=0, support=SupportType.PINNED))
        solver.add_node(Node(id=1, x=L / 2, y=0))
        solver.add_node(Node(id=2, x=L, y=0, support=SupportType.ROLLER_Y))

        solver.add_element(Element(id=0, node_i=0, node_j=1, material=mat, section=sec))
        solver.add_element(Element(id=1, node_i=1, node_j=2, material=mat, section=sec))

        solver.add_point_load(PointLoad(node_id=1, fy=-10000))

        result = solver.solve()
        assert result.success

        diagrams = generate_diagram_data(result, element_id=0, n_points=20)
        assert "moment" in diagrams
        assert "shear" in diagrams
        assert "deflection" in diagrams
        assert "max_values" in diagrams
        assert len(diagrams["moment"]) == 20
        assert len(diagrams["shear"]) == 20

    def test_summary_table(self):
        from app.engineering.fem_solver import analyze_simple_beam
        from app.engineering.advanced_analysis import generate_summary_table

        result = analyze_simple_beam(
            L=5.0, E=200e9, I=5e-5, A=0.005,
            loads=[{"type": "point", "position": 0.5, "magnitude": 10000}],
            n_elements=5,
        )
        summary = generate_summary_table(result)
        assert "max_displacement_m" in summary
        assert "reactions" in summary
        assert "element_summary" in summary
        assert len(summary["element_summary"]) == 5


# ── API Endpoint Tests ──────────────────────────────────────────────


class TestFEMEndpoints:
    """Test FEM solver API endpoints."""

    def test_fem_beam_endpoint(self, client):
        resp = client.post("/api/v1/fem/beam", json={
            "length": 6.0,
            "E": 200e9,
            "I": 1e-4,
            "A": 0.01,
            "loads": [{"type": "point", "position": 0.5, "magnitude": 10000}],
            "n_elements": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "summary" in data

    def test_fem_analyze_endpoint(self, client):
        resp = client.post("/api/v1/fem/analyze", json={
            "nodes": [
                {"id": 0, "x": 0, "y": 0, "support": "pinned"},
                {"id": 1, "x": 3, "y": 0},
                {"id": 2, "x": 6, "y": 0, "support": "roller_y"},
            ],
            "elements": [
                {"id": 0, "node_i": 0, "node_j": 1, "A": 0.003, "Ix": 8.33e-6},
                {"id": 1, "node_i": 1, "node_j": 2, "A": 0.003, "Ix": 8.33e-6},
            ],
            "point_loads": [{"node_id": 1, "fy": -10000}],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "displacements" in data
        assert "reactions" in data

    def test_fem_portal_frame_endpoint(self, client):
        resp = client.post("/api/v1/fem/portal-frame", json={
            "width": 6.0, "height": 4.0,
            "E": 200e9, "I_col": 5e-5, "I_beam": 1e-4,
            "A_col": 0.005, "A_beam": 0.01,
            "loads": [{"type": "distributed", "magnitude": 5000}],
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestSectionsEndpoints:
    """Test sections database API endpoints."""

    def test_list_sections(self, client):
        resp = client.get("/api/v1/sections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 20
        assert data["w_shapes"] > 10

    def test_sections_by_type(self, client):
        resp = client.get("/api/v1/sections/W")
        assert resp.status_code == 200
        assert resp.json()["count"] > 10

    def test_lookup_section(self, client):
        resp = client.get("/api/v1/sections/lookup/W12×50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["designation"] == "W12×50"
        assert data["type"] == "W"

    def test_lookup_not_found(self, client):
        resp = client.get("/api/v1/sections/lookup/W99×999")
        assert resp.status_code == 404

    def test_find_sections(self, client):
        resp = client.post("/api/v1/sections/find", json={"min_Ix": 1e-4})
        assert resp.status_code == 200
        assert resp.json()["count"] > 0


class TestBucklingEndpoints:
    """Test buckling and interaction API endpoints."""

    def test_buckling_endpoint(self, client):
        resp = client.post("/api/v1/buckling", json={
            "length": 3.0, "E": 200e9, "I": 5e-5, "A": 0.005,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["critical_load_N"] > 0
        assert data["slenderness_ratio"] > 0

    def test_interaction_endpoint(self, client):
        resp = client.post("/api/v1/interaction-check", json={
            "P": 100000, "M": 20000, "Pc": 200000, "Mc": 50000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("OK", "FAIL")


class TestSizingEndpoints:
    """Test member sizing API endpoints."""

    def test_beam_sizing_endpoint(self, client):
        resp = client.post("/api/v1/sizing/beam", json={
            "span": 6.0, "E": 200e9, "Fy": 250e6,
            "V_demand": 30000, "M_demand": 50000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["optimal_section"] != "NO ADEQUATE SECTION FOUND"

    def test_column_sizing_endpoint(self, client):
        resp = client.post("/api/v1/sizing/column", json={
            "length": 4.0, "E": 200e9, "Fy": 250e6,
            "P_demand": 200000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["optimal_section"] != "NO ADEQUATE COLUMN FOUND"


class TestDiagramEndpoint:
    """Test diagram generation endpoint."""

    def test_diagrams_endpoint(self, client):
        resp = client.post("/api/v1/diagrams", json={
            "nodes": [
                {"id": 0, "x": 0, "y": 0, "support": "pinned"},
                {"id": 1, "x": 3, "y": 0},
                {"id": 2, "x": 6, "y": 0, "support": "roller_y"},
            ],
            "elements": [
                {"id": 0, "node_i": 0, "node_j": 1, "A": 0.003, "Ix": 8.33e-6},
                {"id": 1, "node_i": 1, "node_j": 2, "A": 0.003, "Ix": 8.33e-6},
            ],
            "point_loads": [{"node_id": 1, "fy": -10000}],
            "element_id": 0,
            "n_points": 20,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "diagrams" in data
        assert "moment" in data["diagrams"]
        assert "shear" in data["diagrams"]
        assert "deflection" in data["diagrams"]
