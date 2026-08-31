from __future__ import annotations

from enum import Enum
from typing import Any

from app.analysis.schemas import (
    AnalysisFinding,
    AnalysisFindingSeverity,
    AnalysisResult,
)


class ComplianceStatus(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


class ComplianceFinding:
    def __init__(
        self,
        rule_id: str,
        status: ComplianceStatus,
        message: str,
        evidence: dict[str, Any] | None = None,
        source: str = "",
    ):
        self.rule_id = rule_id
        self.status = status
        self.message = message
        self.evidence = evidence or {}
        self.source = source


class ComplianceReport:
    def __init__(
        self,
        status: ComplianceStatus,
        findings: list[ComplianceFinding],
        design_version: str = "",
        standard: str = "",
    ):
        self.status = status
        self.findings = findings
        self.design_version = design_version
        self.standard = standard

        self.passed = status is ComplianceStatus.PASS
        self.failed = status is ComplianceStatus.FAIL
        self.requires_review = status is ComplianceStatus.REVIEW

        total = len(findings)
        pass_count = sum(1 for f in findings if f.status is ComplianceStatus.PASS)
        review_count = sum(1 for f in findings if f.status is ComplianceStatus.REVIEW)
        fail_count = sum(1 for f in findings if f.status is ComplianceStatus.FAIL)

        self.summary = {
            "total": total,
            "pass": pass_count,
            "review": review_count,
            "fail": fail_count,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "design_version": self.design_version,
            "standard": self.standard,
            "passed": self.passed,
            "failed": self.failed,
            "requires_review": self.requires_review,
            "summary": self.summary,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "status": f.status.value,
                    "message": f.message,
                    "evidence": f.evidence,
                    "source": f.source,
                }
                for f in self.findings
            ],
        }


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _map_analysis_finding(finding: AnalysisFinding) -> ComplianceFinding:
    code = finding.code
    status = ComplianceStatus.REVIEW

    if finding.severity is AnalysisFindingSeverity.ERROR:
        status = ComplianceStatus.FAIL
    elif finding.severity is AnalysisFindingSeverity.WARNING:
        status = ComplianceStatus.REVIEW
    else:
        status = ComplianceStatus.PASS

    return ComplianceFinding(
        rule_id=f"ANALYSIS:{code}",
        status=status,
        message=finding.message,
        evidence=finding.evidence,
        source="structural_analysis",
    )


def _map_rule_result(result: Any, index: int) -> ComplianceFinding:
    passed = _get_attr(result, "passed")
    if passed is True:
        status = ComplianceStatus.PASS
    elif passed is False:
        status = ComplianceStatus.FAIL
    else:
        rule_status = str(_get_attr(result, "status", "")).upper()
        if rule_status in ("PASS",):
            status = ComplianceStatus.PASS
        elif rule_status in ("FAIL",):
            status = ComplianceStatus.FAIL
        else:
            status = ComplianceStatus.REVIEW

    rule_id = _get_attr(result, "rule_id") or _get_attr(result, "code") or f"RULE-{index + 1:03d}"
    message = _get_attr(result, "message", "")
    evidence = _get_attr(result, "evidence", {})
    source = _get_attr(result, "source", "")

    return ComplianceFinding(
        rule_id=rule_id,
        status=status,
        message=message,
        evidence=evidence if isinstance(evidence, dict) else {},
        source=source,
    )


def _determine_overall_status(findings: list[ComplianceFinding]) -> ComplianceStatus:
    has_fail = any(f.status is ComplianceStatus.FAIL for f in findings)
    has_review = any(f.status is ComplianceStatus.REVIEW for f in findings)

    if has_fail:
        return ComplianceStatus.FAIL
    if has_review:
        return ComplianceStatus.REVIEW
    return ComplianceStatus.PASS


class ComplianceService:
    def evaluate(
        self,
        analysis: AnalysisResult | None = None,
        rule_results: list[Any] | None = None,
        standard: str = "",
    ) -> ComplianceReport:
        findings: list[ComplianceFinding] = []

        if analysis is not None:
            for finding in analysis.findings:
                findings.append(_map_analysis_finding(finding))

        if rule_results:
            for i, result in enumerate(rule_results):
                findings.append(_map_rule_result(result, i))

        status = _determine_overall_status(findings)

        return ComplianceReport(
            status=status,
            findings=findings,
            design_version=analysis.design_version if analysis else "",
            standard=standard,
        )


def evaluate_compliance(
    analysis: AnalysisResult | None = None,
    rule_results: list[Any] | None = None,
    standard: str = "",
) -> ComplianceReport:
    return ComplianceService().evaluate(analysis, rule_results, standard)
