

from dataclasses import dataclass

from app.analysis.schemas import (
    AnalysisFinding,
    AnalysisFindingSeverity,
    AnalysisFindingStatus,
    AnalysisResult,
    AnalysisSummary,
)
from app.compliance.service import (
    ComplianceService,
    ComplianceStatus,
    evaluate_compliance,
)


def analysis_with_findings(*findings):
    summary = AnalysisSummary(
        member_count=2,
        connection_count=1,
        total_member_length_m=9.0,
        total_member_volume_m3=0.07,
        connected_member_count=2,
        disconnected_member_count=0,
        complete_geometry_member_count=2,
        incomplete_geometry_member_count=0,
        finding_count=len(findings),
        error_count=sum(
            finding.severity is AnalysisFindingSeverity.ERROR
            for finding in findings
        ),
        warning_count=sum(
            finding.severity is AnalysisFindingSeverity.WARNING
            for finding in findings
        ),
    )

    return AnalysisResult(
        design_version="DV-001",
        design_type="frame",
        status="complete",
        summary=summary,
        findings=list(findings),
    )


def test_empty_analysis_produces_pass():
    analysis = analysis_with_findings()

    report = evaluate_compliance(analysis)

    assert report.status is ComplianceStatus.PASS
    assert report.passed is True
    assert report.failed is False
    assert report.requires_review is False
    assert report.summary == {
        "total": 0,
        "pass": 0,
        "review": 0,
        "fail": 0,
    }


def test_analysis_failure_becomes_compliance_failure():
    finding = AnalysisFinding(
        code="GEOMETRY-LENGTH-MISMATCH",
        title="Length mismatch",
        severity=AnalysisFindingSeverity.ERROR,
        status=AnalysisFindingStatus.FAIL,
        message="Declared length differs from geometry.",
        evidence={
            "declared_length_m": 4.0,
            "geometric_length_m": 3.0,
        },
    )

    report = evaluate_compliance(
        analysis_with_findings(finding)
    )

    assert report.status is ComplianceStatus.FAIL
    assert report.failed is True
    assert report.summary["fail"] == 1

    result = report.findings[0]

    assert result.rule_id == "ANALYSIS:GEOMETRY-LENGTH-MISMATCH"
    assert result.source == "structural_analysis"
    assert result.evidence["declared_length_m"] == 4.0


def test_analysis_review_becomes_compliance_review():
    finding = AnalysisFinding(
        code="GEOMETRY-INCOMPLETE",
        title="Incomplete geometry",
        severity=AnalysisFindingSeverity.WARNING,
        status=AnalysisFindingStatus.REVIEW,
        message="Coordinates are incomplete.",
        evidence={"member_id": "M-003"},
    )

    report = evaluate_compliance(
        analysis_with_findings(finding)
    )

    assert report.status is ComplianceStatus.REVIEW
    assert report.requires_review is True
    assert report.summary["review"] == 1


def test_rule_mapping_accepts_dictionary_results():
    analysis = analysis_with_findings()

    rule_results = [
        {
            "rule_id": "SPHERE-GEO-001",
            "title": "Minimum geometry",
            "status": "pass",
            "severity": "info",
            "message": "Requirement satisfied.",
            "evidence": {
                "actual_m": 6.0,
                "required_m": 5.0,
            },
            "source": "Sphere Handbook",
        }
    ]

    report = evaluate_compliance(
        analysis,
        rule_results,
    )

    assert report.status is ComplianceStatus.PASS
    assert report.summary["pass"] == 1

    finding = report.findings[0]

    assert finding.rule_id == "SPHERE-GEO-001"
    assert finding.evidence["actual_m"] == 6.0
    assert finding.source == "Sphere Handbook"


def test_rule_failure_takes_precedence_over_review():
    analysis = analysis_with_findings(
        AnalysisFinding(
            code="GEOMETRY-INCOMPLETE",
            title="Incomplete geometry",
            severity=AnalysisFindingSeverity.WARNING,
            status=AnalysisFindingStatus.REVIEW,
            message="Review required.",
            evidence={},
        )
    )

    rule_results = [
        {
            "rule_id": "SPHERE-001",
            "status": "fail",
            "severity": "error",
            "message": "Requirement failed.",
        }
    ]

    report = evaluate_compliance(
        analysis,
        rule_results,
    )

    assert report.status is ComplianceStatus.FAIL
    assert report.summary["review"] == 1
    assert report.summary["fail"] == 1


def test_review_takes_precedence_over_pass():
    analysis = analysis_with_findings()

    rule_results = [
        {
            "rule_id": "SPHERE-001",
            "status": "pass",
            "message": "Passed.",
        },
        {
            "rule_id": "SPHERE-002",
            "status": "not_evaluated",
            "message": "Load data unavailable.",
        },
    ]

    report = evaluate_compliance(
        analysis,
        rule_results,
    )

    assert report.status is ComplianceStatus.REVIEW
    assert report.summary["pass"] == 1
    assert report.summary["review"] == 1


def test_boolean_rule_result_is_supported():
    analysis = analysis_with_findings()

    rule_results = [
        {
            "code": "SPHERE-001",
            "passed": True,
            "message": "Satisfied.",
        },
        {
            "code": "SPHERE-002",
            "passed": False,
            "message": "Failed.",
        },
    ]

    report = evaluate_compliance(
        analysis,
        rule_results,
    )

    assert report.status is ComplianceStatus.FAIL
    assert report.summary["pass"] == 1
    assert report.summary["fail"] == 1


@dataclass
class RuleObject:
    rule_id: str
    title: str
    status: str
    severity: str
    message: str
    evidence: dict
    source: str


def test_rule_object_results_are_supported():
    analysis = analysis_with_findings()

    result = RuleObject(
        rule_id="SPHERE-OBJ-001",
        title="Object rule",
        status="pass",
        severity="info",
        message="Passed.",
        evidence={"actual": 10},
        source="Sphere Handbook",
    )

    report = ComplianceService().evaluate(
        analysis,
        [result],
    )

    assert report.status is ComplianceStatus.PASS
    assert report.findings[0].rule_id == "SPHERE-OBJ-001"


def test_pydantic_rule_results_are_supported():
    from pydantic import BaseModel

    class PydanticRuleResult(BaseModel):
        rule_id: str
        status: str
        message: str
        evidence: dict[str, object]

    analysis = analysis_with_findings()

    result = PydanticRuleResult(
        rule_id="SPHERE-PYD-001",
        status="pass",
        message="Passed.",
        evidence={"value": 12},
    )

    report = evaluate_compliance(
        analysis,
        [result],
    )

    assert report.status is ComplianceStatus.PASS
    assert report.findings[0].evidence["value"] == 12


def test_missing_rule_status_defaults_to_review():
    analysis = analysis_with_findings()

    report = evaluate_compliance(
        analysis,
        [
            {
                "rule_id": "SPHERE-UNKNOWN-001",
                "message": "Insufficient evidence.",
            }
        ],
    )

    assert report.status is ComplianceStatus.REVIEW
    assert report.summary["review"] == 1


def test_unknown_rule_id_gets_deterministic_fallback():
    analysis = analysis_with_findings()

    report = evaluate_compliance(
        analysis,
        [
            {"status": "pass", "message": "First."},
            {"status": "pass", "message": "Second."},
        ],
    )

    assert report.findings[0].rule_id == "RULE-001"
    assert report.findings[1].rule_id == "RULE-002"


def test_not_evaluated_is_not_reported_as_pass():
    analysis = analysis_with_findings()

    report = evaluate_compliance(
        analysis,
        [
            {
                "rule_id": "SPHERE-WIND-001",
                "status": "NOT_EVALUATED",
                "message": "Wind load data unavailable.",
            }
        ],
    )

    assert report.status is ComplianceStatus.REVIEW
    assert report.findings[0].status is ComplianceStatus.REVIEW


def test_frontend_payload_is_stable():
    finding = AnalysisFinding(
        code="TEST-001",
        title="Test",
        severity=AnalysisFindingSeverity.WARNING,
        status=AnalysisFindingStatus.REVIEW,
        message="Review.",
        evidence={"actual": 3},
    )

    report = evaluate_compliance(
        analysis_with_findings(finding),
        standard="Sphere Handbook",
    )

    payload = report.to_dict()

    assert payload["status"] == "review"
    assert payload["design_version"] == "DV-001"
    assert payload["standard"] == "Sphere Handbook"
    assert payload["requires_review"] is True
    assert payload["failed"] is False

    assert payload["findings"][0]["rule_id"] == (
        "ANALYSIS:TEST-001"
    )
    assert payload["findings"][0]["evidence"]["actual"] == 3


def test_no_mutation_of_analysis_findings():
    finding = AnalysisFinding(
        code="TEST-001",
        title="Test",
        severity=AnalysisFindingSeverity.WARNING,
        status=AnalysisFindingStatus.REVIEW,
        message="Review.",
        evidence={"actual": 3},
    )

    analysis = analysis_with_findings(finding)

    before = analysis.model_dump()

    evaluate_compliance(
        analysis,
        [
            {
                "rule_id": "SPHERE-001",
                "status": "pass",
            }
        ],
    )

    after = analysis.model_dump()

    assert before == after