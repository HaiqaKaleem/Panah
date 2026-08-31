
from app.analysis.schemas import (
    AnalysisFinding,
    AnalysisFindingSeverity,
    AnalysisFindingStatus,
    AnalysisResult,
    AnalysisSummary,
    MemberAnalysis,
)


def test_analysis_finding_is_structured():
    finding = AnalysisFinding(
        code="TEST-001",
        title="Test finding",
        severity=AnalysisFindingSeverity.WARNING,
        status=AnalysisFindingStatus.REVIEW,
        message="Review required.",
        evidence={"value": 10},
    )

    assert finding.code == "TEST-001"
    assert finding.severity is AnalysisFindingSeverity.WARNING
    assert finding.status is AnalysisFindingStatus.REVIEW
    assert finding.evidence["value"] == 10


def test_member_analysis_accepts_computed_metrics():
    result = MemberAnalysis(
        member_id="M-001",
        member_type="beam",
        material_id="MAT-001",
        length_m=5.0,
        geometric_length_m=5.0,
        diameter_m=0.1,
        volume_m3=0.0392699,
        geometry_complete=True,
        connected=True,
    )

    assert result.member_id == "M-001"
    assert result.geometry_complete is True
    assert result.connected is True


def test_analysis_summary_defaults_are_valid():
    summary = AnalysisSummary(
        member_count=2,
        connection_count=1,
        total_member_length_m=10.0,
        total_member_volume_m3=0.1,
        connected_member_count=2,
        disconnected_member_count=0,
        complete_geometry_member_count=2,
        incomplete_geometry_member_count=0,
        finding_count=0,
        error_count=0,
        warning_count=0,
    )

    assert summary.member_count == 2
    assert summary.total_member_length_m == 10.0


def test_analysis_result_reports_error_state():
    summary = AnalysisSummary(
        member_count=1,
        connection_count=0,
        total_member_length_m=5.0,
        total_member_volume_m3=0.0,
        connected_member_count=0,
        disconnected_member_count=1,
        complete_geometry_member_count=1,
        incomplete_geometry_member_count=0,
        finding_count=1,
        error_count=1,
        warning_count=0,
    )

    result = AnalysisResult(
        design_version="DV-001",
        design_type="frame",
        status="requires_review",
        summary=summary,
    )

    assert result.has_errors is True
    assert result.requires_review is True


def test_analysis_result_to_dict_is_frontend_ready():
    summary = AnalysisSummary(
        member_count=1,
        connection_count=1,
        total_member_length_m=5.0,
        total_member_volume_m3=0.0,
        connected_member_count=1,
        disconnected_member_count=0,
        complete_geometry_member_count=1,
        incomplete_geometry_member_count=0,
        finding_count=0,
        error_count=0,
        warning_count=0,
    )

    result = AnalysisResult(
        design_version="DV-001",
        design_type="frame",
        status="complete",
        summary=summary,
    )

    payload = result.to_dict()

    assert payload["analysis_version"] == "1.0.0"
    assert payload["design_version"] == "DV-001"
    assert payload["status"] == "complete"
    assert payload["summary"]["member_count"] == 1
    assert payload["has_errors"] is False
    assert payload["requires_review"] is False