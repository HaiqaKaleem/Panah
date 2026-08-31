
import math

import pytest

from app.analysis.schemas import (
    AnalysisFindingSeverity,
    AnalysisFindingStatus,
)
from app.analysis.service import (
    StructuralAnalysisService,
    analyze_design,
)
from app.schemas.design_version import (
    CanonicalDesignVersion,
    DesignConnection,
    DesignMember,
    DesignMetadata,
    DesignPoint3D,
)


def valid_design() -> CanonicalDesignVersion:
    return CanonicalDesignVersion(
        schema_version="1.0.0",
        design_type="frame",
        version="DV-001",
        span_m=6.0,
        height_m=3.0,
        members=[
            DesignMember(
                id="M-001",
                type="column",
                material_id="MAT-001",
                start=DesignPoint3D(
                    x_m=0,
                    y_m=0,
                    z_m=0,
                ),
                end=DesignPoint3D(
                    x_m=0,
                    y_m=0,
                    z_m=3,
                ),
                length_m=3.0,
                diameter_m=0.1,
            ),
            DesignMember(
                id="M-002",
                type="beam",
                material_id="MAT-001",
                start=DesignPoint3D(
                    x_m=0,
                    y_m=0,
                    z_m=3,
                ),
                end=DesignPoint3D(
                    x_m=6,
                    y_m=0,
                    z_m=3,
                ),
                length_m=6.0,
                diameter_m=0.1,
            ),
        ],
        connections=[
            DesignConnection(
                id="C-001",
                a="M-001",
                b="M-002",
                type="bolted",
            ),
        ],
        metadata=DesignMetadata(
            generator_name="local",
            generator_version="1.0.0",
        ),
    )


def test_service_returns_analysis_result():
    result = analyze_design(valid_design())

    assert result.design_version == "DV-001"
    assert result.design_type == "frame"
    assert result.analysis_version == "1.0.0"


def test_member_geometry_is_calculated():
    result = analyze_design(valid_design())

    first = next(
        member
        for member in result.members
        if member.member_id == "M-001"
    )

    second = next(
        member
        for member in result.members
        if member.member_id == "M-002"
    )

    assert first.geometric_length_m == pytest.approx(3.0)
    assert second.geometric_length_m == pytest.approx(6.0)

    assert first.geometry_complete is True
    assert second.geometry_complete is True


def test_total_member_length_is_calculated():
    result = analyze_design(valid_design())

    assert result.summary.total_member_length_m == pytest.approx(9.0)


def test_cylindrical_member_volume_is_calculated():
    result = analyze_design(valid_design())

    first = next(
        member
        for member in result.members
        if member.member_id == "M-001"
    )

    expected = math.pi * (0.1 / 2) ** 2 * 3.0

    assert first.volume_m3 == pytest.approx(expected)


def test_total_volume_is_calculated():
    result = analyze_design(valid_design())

    expected = (
        math.pi * (0.1 / 2) ** 2 * 3.0
        + math.pi * (0.1 / 2) ** 2 * 6.0
    )

    assert result.summary.total_member_volume_m3 == pytest.approx(
        expected,
        rel=1e-9,
    )


def test_connected_members_are_counted():
    result = analyze_design(valid_design())

    assert result.summary.connected_member_count == 2
    assert result.summary.disconnected_member_count == 0


def test_no_connections_creates_structural_network_error():
    design = valid_design()

    design = design.model_copy(
        update={
            "connections": [],
        }
    )

    result = analyze_design(design)

    assert result.has_errors is True
    assert result.status == "requires_review"

    network_finding = next(
        finding
        for finding in result.findings
        if finding.code == "DESIGN-NETWORK-UNCONNECTED"
    )

    assert network_finding.severity is AnalysisFindingSeverity.ERROR
    assert network_finding.status is AnalysisFindingStatus.FAIL


def test_disconnected_member_creates_warning():
    design = valid_design()

    design = design.model_copy(
        update={
            "members": [
                *design.members,
                DesignMember(
                    id="M-003",
                    type="brace",
                    material_id="MAT-001",
                    length_m=2.0,
                    diameter_m=0.05,
                ),
            ]
        }
    )

    result = analyze_design(design)

    assert result.summary.disconnected_member_count == 1

    finding = next(
        finding
        for finding in result.findings
        if finding.code == "MEMBER-DISCONNECTED"
        and finding.evidence["member_id"] == "M-003"
    )

    assert finding.severity is AnalysisFindingSeverity.WARNING
    assert finding.status is AnalysisFindingStatus.REVIEW


def test_incomplete_geometry_is_flagged_for_review():
    design = valid_design()

    design = design.model_copy(
        update={
            "members": [
                DesignMember(
                    id="M-003",
                    type="brace",
                    material_id="MAT-001",
                    length_m=2.0,
                    diameter_m=0.05,
                ),
            ]
        }
    )

    result = analyze_design(design)

    member = result.members[0]

    assert member.geometry_complete is False
    assert member.geometric_length_m is None

    finding = next(
        finding
        for finding in result.findings
        if finding.code == "GEOMETRY-INCOMPLETE"
    )

    assert finding.status is AnalysisFindingStatus.REVIEW


def test_declared_and_geometric_length_mismatch_is_error():
    design = valid_design()

    bad_member = design.members[0].model_copy(
        update={
            "length_m": 4.0,
        }
    )

    design = design.model_copy(
        update={
            "members": [
                bad_member,
                design.members[1],
            ]
        }
    )

    result = analyze_design(design)

    finding = next(
        finding
        for finding in result.findings
        if finding.code == "GEOMETRY-LENGTH-MISMATCH"
    )

    assert finding.severity is AnalysisFindingSeverity.ERROR
    assert finding.status is AnalysisFindingStatus.FAIL

    assert finding.evidence["declared_length_m"] == 4.0
    assert finding.evidence["geometric_length_m"] == pytest.approx(3.0)


def test_small_length_difference_within_tolerance_passes():
    design = valid_design()

    member = design.members[0].model_copy(
        update={
            "length_m": 3.005,
        }
    )

    design = design.model_copy(
        update={
            "members": [
                member,
                design.members[1],
            ]
        }
    )

    result = analyze_design(design)

    mismatch_findings = [
        finding
        for finding in result.findings
        if finding.code == "GEOMETRY-LENGTH-MISMATCH"
    ]

    assert mismatch_findings == []


def test_length_difference_above_tolerance_fails():
    design = valid_design()

    member = design.members[0].model_copy(
        update={
            "length_m": 3.02,
        }
    )

    design = design.model_copy(
        update={
            "members": [
                member,
                design.members[1],
            ]
        }
    )

    result = analyze_design(design)

    assert any(
        finding.code == "GEOMETRY-LENGTH-MISMATCH"
        for finding in result.findings
    )


def test_analysis_with_complete_connected_geometry_is_complete():
    result = analyze_design(valid_design())

    assert result.status == "complete"
    assert result.summary.error_count == 0
    assert result.summary.warning_count == 0
    assert result.summary.complete_geometry_member_count == 2
    assert result.summary.incomplete_geometry_member_count == 0


def test_service_class_and_function_have_same_behavior():
    design = valid_design()

    direct = StructuralAnalysisService().analyze(design)
    convenience = analyze_design(design)

    assert direct.model_dump() == convenience.model_dump()


def test_analysis_does_not_claim_engineering_safety():
    result = analyze_design(valid_design())

    payload = result.to_dict()

    assert "safe" not in payload
    assert "approved" not in payload
    assert "engineering_approval" not in payload