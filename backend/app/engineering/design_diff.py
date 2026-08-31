"""
Design Diff Engine — Compare Two Design Versions

Produces a structured diff between two CanonicalDesignVersions,
showing changes in members, connections, geometry, and materials.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DesignChange:
    """A single change between two designs."""
    category: str  # "member_added", "member_removed", "member_modified", "connection_changed", "geometry_changed"
    element_id: str
    description: str
    old_value: Any = None
    new_value: Any = None
    impact: str = "neutral"  # "positive", "negative", "neutral"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "element_id": self.element_id,
            "description": self.description,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "impact": self.impact,
        }


@dataclass
class DesignDiffResult:
    """Complete diff between two designs."""
    design_a_id: str
    design_b_id: str
    changes: list[DesignChange]
    summary: dict[str, Any]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "design_a_id": self.design_a_id,
            "design_b_id": self.design_b_id,
            "changes": [c.to_dict() for c in self.changes],
            "summary": self.summary,
            "recommendation": self.recommendation,
        }


def compute_design_diff(
    design_a: dict[str, Any],
    design_b: dict[str, Any],
) -> DesignDiffResult:
    """
    Compare two designs and return a structured diff.

    Args:
        design_a: First design (dict from CanonicalDesignVersion.model_dump()).
        design_b: Second design (dict from CanonicalDesignVersion.model_dump()).

    Returns:
        DesignDiffResult with changes, summary, and recommendation.
    """
    changes: list[DesignChange] = []
    a_id = design_a.get("version", "A")
    b_id = design_b.get("version", "B")

    # --- Geometry changes ---
    for field_name, label in [("span_m", "Span"), ("height_m", "Height")]:
        val_a = design_a.get(field_name, 0)
        val_b = design_b.get(field_name, 0)
        if val_a != val_b:
            impact = "positive" if field_name == "height_m" and val_b > val_a else "negative" if field_name == "height_m" and val_b < val_a else "neutral"
            changes.append(DesignChange(
                category="geometry_changed",
                element_id=field_name,
                description=f"{label} changed from {val_a}m to {val_b}m",
                old_value=val_a,
                new_value=val_b,
                impact=impact,
            ))

    # --- Member changes ---
    members_a = {m["id"]: m for m in design_a.get("members", [])}
    members_b = {m["id"]: m for m in design_b.get("members", [])}

    added = set(members_b.keys()) - set(members_a.keys())
    removed = set(members_a.keys()) - set(members_b.keys())
    common = set(members_a.keys()) & set(members_b.keys())

    for mid in sorted(added):
        m = members_b[mid]
        changes.append(DesignChange(
            category="member_added",
            element_id=mid,
            description=f"Added {m.get('type', 'unknown')} member ({m.get('material_id', 'N/A')})",
            new_value=m.get("type"),
            impact="positive",
        ))

    for mid in sorted(removed):
        m = members_a[mid]
        changes.append(DesignChange(
            category="member_removed",
            element_id=mid,
            description=f"Removed {m.get('type', 'unknown')} member",
            old_value=m.get("type"),
            impact="negative",
        ))

    for mid in sorted(common):
        ma = members_a[mid]
        mb = members_b[mid]
        diffs = []
        for key in ["type", "material_id", "length_m", "diameter_m"]:
            if ma.get(key) != mb.get(key):
                diffs.append(key)
        if diffs:
            changes.append(DesignChange(
                category="member_modified",
                element_id=mid,
                description=f"Modified {', '.join(diffs)}",
                old_value={k: ma.get(k) for k in diffs},
                new_value={k: mb.get(k) for k in diffs},
                impact="neutral",
            ))

    # --- Connection changes ---
    conns_a = {c["id"]: c for c in design_a.get("connections", [])}
    conns_b = {c["id"]: c for c in design_b.get("connections", [])}

    conn_added = set(conns_b.keys()) - set(conns_a.keys())
    conn_removed = set(conns_a.keys()) - set(conns_b.keys())

    for cid in sorted(conn_added):
        c = conns_b[cid]
        changes.append(DesignChange(
            category="connection_added",
            element_id=cid,
            description=f"Added connection ({c.get('type', 'N/A')}): {c.get('a', '?')} → {c.get('b', '?')}",
            impact="positive",
        ))

    for cid in sorted(conn_removed):
        changes.append(DesignChange(
            category="connection_removed",
            element_id=cid,
            description=f"Removed connection",
            impact="negative",
        ))

    # --- Summary ---
    member_changes = sum(1 for c in changes if c.category.startswith("member_"))
    conn_changes = sum(1 for c in changes if c.category.startswith("connection_"))
    geo_changes = sum(1 for c in changes if c.category == "geometry_changed")
    positive = sum(1 for c in changes if c.impact == "positive")
    negative = sum(1 for c in changes if c.impact == "negative")

    members_a_count = len(members_a)
    members_b_count = len(members_b)

    summary = {
        "total_changes": len(changes),
        "member_changes": member_changes,
        "connection_changes": conn_changes,
        "geometry_changes": geo_changes,
        "positive_impacts": positive,
        "negative_impacts": negative,
        "members_a": members_a_count,
        "members_b": members_b_count,
        "member_count_change": members_b_count - members_a_count,
    }

    # --- Recommendation ---
    if negative == 0 and positive > 0:
        recommendation = f"Design {b_id} is an improvement over {a_id} with {positive} positive changes and no negative impacts."
    elif negative > positive:
        recommendation = f"Design {b_id} has {negative} negative impacts compared to {a_id}. Review recommended before adoption."
    elif len(changes) == 0:
        recommendation = f"Designs {a_id} and {b_id} are identical."
    else:
        recommendation = f"Mixed changes between {a_id} and {b_id}. {positive} positive, {negative} negative. Engineering review required."

    return DesignDiffResult(
        design_a_id=a_id,
        design_b_id=b_id,
        changes=changes,
        summary=summary,
        recommendation=recommendation,
    )
