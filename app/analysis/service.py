
from __future__ import annotations

import math

from app.analysis.schemas import (
    AnalysisFinding,
    AnalysisFindingSeverity,
    AnalysisFindingStatus,
    AnalysisResult,
    AnalysisSummary,
    MemberAnalysis,
)
from app.schemas.design_version import CanonicalDesignVersion, DesignMember


class StructuralAnalysisService:
    """
    Deterministic structural-analysis prescreen.

    This service operates on CanonicalDesignVersion and deliberately
    separates geometric/structural facts from standards compliance.

    It does NOT perform finite-element analysis or claim engineering
    safety approval.
    """

    ANALYSIS_VERSION = "1.0.0"

    LENGTH_TOLERANCE_M = 0.01

    def analyze(
        self,
        design: CanonicalDesignVersion,
    ) -> AnalysisResult:
        member_ids = {member.id for member in design.members}

        connected_member_ids: set[str] = set()

        for connection in design.connections:
            connected_member_ids.add(connection.a)
            connected_member_ids.add(connection.b)

        findings: list[AnalysisFinding] = []
        member_results: list[MemberAnalysis] = []

        total_length = 0.0
        total_volume = 0.0

    


        connected_count = 0
        disconnected_count = 0

        complete_geometry_count = 0
        incomplete_geometry_count = 0

        for member in design.members:
            geometric_length = self._geometric_length(member)

            geometry_complete = geometric_length is not None

            if geometry_complete:
                complete_geometry_count += 1
            else:
                incomplete_geometry_count += 1

            declared_length = member.length_m

            if declared_length is not None:
                effective_length = declared_length
            else:
                effective_length = geometric_length

            if effective_length is not None:
                total_length += effective_length

            volume = self._member_volume(member, effective_length)

            if volume is not None:
                total_volume += volume

            connected = member.id in connected_member_ids

            if connected:
                connected_count += 1
            else:
                disconnected_count += 1

            member_results.append(
                MemberAnalysis(
                    member_id=member.id,
                    member_type=member.type,
                    material_id=member.material_id,
                    length_m=declared_length,
                    geometric_length_m=geometric_length,
                    diameter_m=member.diameter_m,
                    volume_m3=volume,
                    geometry_complete=geometry_complete,
                    connected=connected,
                )
            )

            findings.extend(
                self._member_findings(
                    member=member,
                    geometric_length=geometric_length,
                    connected=connected,
                )
            )

        findings.extend(
            self._design_findings(
                design=design,
                member_ids=member_ids,
                connected_member_ids=connected_member_ids,
            )
        )

        error_count = sum(
            finding.severity is AnalysisFindingSeverity.ERROR
            for finding in findings
        )

        warning_count = sum(
            finding.severity is AnalysisFindingSeverity.WARNING
            for finding in findings
        )

        summary = AnalysisSummary(
            member_count=len(design.members),
            connection_count=len(design.connections),
            total_member_length_m=round(total_length, 6),
            total_member_volume_m3=total_volume,
    
            connected_member_count=connected_count,
            disconnected_member_count=disconnected_count,
            complete_geometry_member_count=complete_geometry_count,
            incomplete_geometry_member_count=incomplete_geometry_count,
            finding_count=len(findings),
            error_count=error_count,
            warning_count=warning_count,
        )

        status = self._overall_status(
            error_count=error_count,
            warning_count=warning_count,
        )

        return AnalysisResult(
            analysis_version=self.ANALYSIS_VERSION,
            design_version=design.version,
            design_type=design.design_type,
            status=status,
            summary=summary,
            members=member_results,
            findings=findings,
        )

    def _geometric_length(
        self,
        member: DesignMember,
    ) -> float | None:
        if member.start is None or member.end is None:
            return None

        dx = member.end.x_m - member.start.x_m
        dy = member.end.y_m - member.start.y_m
        dz = member.end.z_m - member.start.z_m

        length = math.sqrt(
            dx * dx +
            dy * dy +
            dz * dz
        )

        return round(length, 9)

    def _member_volume(
        self,
        member: DesignMember,
        length_m: float | None,
    ) -> float | None:
        if length_m is None:
            return None

        if member.diameter_m is None:
            return None

        radius = member.diameter_m / 2.0

        volume = math.pi * radius * radius * length_m

        return round(volume, 12)

    def _member_findings(
        self,
        member: DesignMember,
        geometric_length: float | None,
        connected: bool,
    ) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        if (
            member.length_m is not None
            and geometric_length is not None
            and abs(member.length_m - geometric_length)
            > self.LENGTH_TOLERANCE_M
        ):
            findings.append(
                AnalysisFinding(
                    code="GEOMETRY-LENGTH-MISMATCH",
                    title="Declared and geometric length differ",
                    severity=AnalysisFindingSeverity.ERROR,
                    status=AnalysisFindingStatus.FAIL,
                    message=(
                        f"Member {member.id} declares "
                        f"{member.length_m:.3f} m but its coordinates "
                        f"produce {geometric_length:.3f} m."
                    ),
                    evidence={
                        "member_id": member.id,
                        "declared_length_m": member.length_m,
                        "geometric_length_m": geometric_length,
                        "tolerance_m": self.LENGTH_TOLERANCE_M,
                    },
                )
            )

        if not connected:
            findings.append(
                AnalysisFinding(
                    code="MEMBER-DISCONNECTED",
                    title="Member has no connection",
                    severity=AnalysisFindingSeverity.WARNING,
                    status=AnalysisFindingStatus.REVIEW,
                    message=(
                        f"Member {member.id} is not referenced by any "
                        "design connection."
                    ),
                    evidence={
                        "member_id": member.id,
                        "member_type": member.type,
                    },
                )
            )

        if geometric_length is None:
            findings.append(
                AnalysisFinding(
                    code="GEOMETRY-INCOMPLETE",
                    title="Member coordinate geometry unavailable",
                    severity=AnalysisFindingSeverity.WARNING,
                    status=AnalysisFindingStatus.REVIEW,
                    message=(
                        f"Member {member.id} does not contain both start "
                        "and end coordinates. Geometric length cannot "
                        "be independently calculated."
                    ),
                    evidence={
                        "member_id": member.id,
                        "has_start": member.start is not None,
                        "has_end": member.end is not None,
                    },
                )
            )

        return findings

    def _design_findings(
        self,
        design: CanonicalDesignVersion,
        member_ids: set[str],
        connected_member_ids: set[str],
    ) -> list[AnalysisFinding]:
        del member_ids

        findings: list[AnalysisFinding] = []

        if not design.connections:
            findings.append(
                AnalysisFinding(
                    code="DESIGN-NO-CONNECTIONS",
                    title="No structural connections defined",
                    severity=AnalysisFindingSeverity.WARNING,
                    status=AnalysisFindingStatus.REVIEW,
                    message=(
                        "The canonical design contains members but no "
                        "structural connections."
                    ),
                    evidence={
                        "member_count": len(design.members),
                        "connection_count": 0,
                    },
                )
            )

        if design.members and not connected_member_ids:
            findings.append(
                AnalysisFinding(
                    code="DESIGN-NETWORK-UNCONNECTED",
                    title="Structural member network is unconnected",
                    severity=AnalysisFindingSeverity.ERROR,
                    status=AnalysisFindingStatus.FAIL,
                    message=(
                        "No design member participates in a connection. "
                        "Structural load paths cannot be inferred."
                    ),
                    evidence={
                        "member_count": len(design.members),
                        "connection_count": len(design.connections),
                    },
                )
            )

        return findings

    @staticmethod
    def _overall_status(
        error_count: int,
        warning_count: int,
    ) -> str:
        if error_count > 0:
            return "requires_review"

        if warning_count > 0:
            return "review"

        return "complete"


def analyze_design(
    design: CanonicalDesignVersion,
) -> AnalysisResult:
    """Convenience entry point for the structural analysis service."""
    return StructuralAnalysisService().analyze(design)