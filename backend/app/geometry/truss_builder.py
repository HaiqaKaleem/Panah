"""
Panah Truss Geometry Builder.

Computes actual 3D coordinates for roof truss members from
ConstraintSet parameters. This produces renderer-ready data
for Three.js, unlike the basic geometry builder which requires
pre-existing coordinates.

For a simple triangular roof truss:

        P2 (peak)
       / | \
      /  |  \
     /   |   \
    /    |    \
   P0 ---P1--- P3  (bottom chord)

Members:
- Bottom chord: P0 → P3 (horizontal beam)
- Left rafter:  P0 → P2 (angled beam)
- Right rafter: P3 → P2 (angled beam)
- King post:    P1 → P2 (vertical brace, center)
- Optional: diagonal braces
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float

    def to_dict(self) -> dict:
        return {"x": round(self.x, 4), "y": round(self.y, 4), "z": round(self.z, 4)}

    def distance_to(self, other: Point3D) -> float:
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )


@dataclass
class TrussMember:
    id: str
    member_type: str  # beam, brace, column, rafter
    material_id: str
    start: Point3D
    end: Point3D
    length_m: float
    diameter_m: float
    label: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.member_type,
            "material_id": self.material_id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "length_m": round(self.length_m, 4),
            "diameter_m": round(self.diameter_m, 4),
            "label": self.label,
            "description": self.description,
        }


@dataclass
class TrussConnection:
    id: str
    a: str
    b: str
    connection_type: str
    point: Point3D

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "a": self.a,
            "b": self.b,
            "type": self.connection_type,
            "point": self.point.to_dict(),
        }


@dataclass
class TrussGeometry:
    design_type: str
    span_m: float
    height_m: float
    width_m: float
    members: list[TrussMember] = field(default_factory=list)
    connections: list[TrussConnection] = field(default_factory=list)
    nodes: dict[str, Point3D] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "design_type": self.design_type,
            "span_m": round(self.span_m, 4),
            "height_m": round(self.height_m, 4),
            "width_m": round(self.width_m, 4),
            "members": [m.to_dict() for m in self.members],
            "connections": [c.to_dict() for c in self.connections],
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "bounding_box": self._bounding_box(),
            "center": self._center(),
            "total_member_length_m": round(sum(m.length_m for m in self.members), 4),
            "member_count": len(self.members),
            "connection_count": len(self.connections),
        }

    def _bounding_box(self) -> dict:
        all_x = [p.x for p in self.nodes.values()]
        all_y = [p.y for p in self.nodes.values()]
        all_z = [p.z for p in self.nodes.values()]
        if not all_x:
            return {"min": {"x": 0, "y": 0, "z": 0}, "max": {"x": 0, "y": 0, "z": 0}}
        return {
            "min": {"x": round(min(all_x), 4), "y": round(min(all_y), 4), "z": round(min(all_z), 4)},
            "max": {"x": round(max(all_x), 4), "y": round(max(all_y), 4), "z": round(max(all_z), 4)},
        }

    def _center(self) -> dict:
        all_x = [p.x for p in self.nodes.values()]
        all_y = [p.y for p in self.nodes.values()]
        all_z = [p.z for p in self.nodes.values()]
        if not all_x:
            return {"x": 0, "y": 0, "z": 0}
        return {
            "x": round((min(all_x) + max(all_x)) / 2, 4),
            "y": round((min(all_y) + max(all_y)) / 2, 4),
            "z": round((min(all_z) + max(all_z)) / 2, 4),
        }


def build_simple_truss(
    span_m: float,
    height_m: float,
    material_id: str,
    diameter_m: float = 0.08,
    width_m: float = 5.0,
    brace_count: int = 1,
) -> TrussGeometry:
    """
    Build a triangular roof truss with actual 3D coordinates.

    The truss lies in the X-Y plane (X = span, Y = height),
    with Z representing the width (depth into the roof).

    Parameters:
        span_m: Horizontal span of the truss
        height_m: Height at the peak (ridge)
        material_id: Material identifier for all members
        diameter_m: Member diameter in meters
        width_m: Width of the shelter (depth perpendicular to truss)
        brace_count: Number of diagonal braces (1 or 2)
    """
    truss = TrussGeometry(
        design_type="roof_truss",
        span_m=span_m,
        height_m=height_m,
        width_m=width_m,
    )

    # --- Key nodes (front truss, Z=0) ---
    # P0: left bottom, P1: center bottom, P2: peak, P3: right bottom
    half_span = span_m / 2

    P0 = Point3D(x=0, y=0, z=0)
    P1 = Point3D(x=half_span, y=0, z=0)  # center bottom (king post base)
    P2 = Point3D(x=half_span, y=height_m, z=0)  # peak
    P3 = Point3D(x=span_m, y=0, z=0)  # right bottom

    truss.nodes = {"P0": P0, "P1": P1, "P2": P2, "P3": P3}

    # --- Bottom chord (horizontal beam) ---
    truss.members.append(TrussMember(
        id="M-BOTTOM",
        member_type="beam",
        material_id=material_id,
        start=P0,
        end=P3,
        length_m=P0.distance_to(P3),
        diameter_m=diameter_m,
        label="Bottom Chord",
        description=f"Horizontal tie beam spanning {span_m:.1f}m",
    ))

    # --- Left rafter ---
    truss.members.append(TrussMember(
        id="M-LEFT-RAFTER",
        member_type="rafter",
        material_id=material_id,
        start=P0,
        end=P2,
        length_m=P0.distance_to(P2),
        diameter_m=diameter_m,
        label="Left Rafter",
        description=f"Left slope rafter, {P0.distance_to(P2):.2f}m",
    ))

    # --- Right rafter ---
    truss.members.append(TrussMember(
        id="M-RIGHT-RAFTER",
        member_type="rafter",
        material_id=material_id,
        start=P3,
        end=P2,
        length_m=P3.distance_to(P2),
        diameter_m=diameter_m,
        label="Right Rafter",
        description=f"Right slope rafter, {P3.distance_to(P2):.2f}m",
    ))

    # --- King post (vertical brace from center bottom to peak) ---
    truss.members.append(TrussMember(
        id="M-KING-POST",
        member_type="column",
        material_id=material_id,
        start=P1,
        end=P2,
        length_m=P1.distance_to(P2),
        diameter_m=diameter_m,
        label="King Post",
        description=f"Vertical king post, {height_m:.2f}m",
    ))

    # --- Diagonal braces ---
    if brace_count >= 1:
        # Left diagonal: from ~quarter point on bottom to mid-height on left rafter
        qx = span_m * 0.25
        qy = 0
        left_mid = Point3D(
            x=(P0.x + P2.x) / 2,
            y=(P0.y + P2.y) / 2,
            z=0,
        )
        brace_start_l = Point3D(x=qx, y=qy, z=0)
        truss.members.append(TrussMember(
            id="M-BRACE-L",
            member_type="brace",
            material_id=material_id,
            start=brace_start_l,
            end=left_mid,
            length_m=brace_start_l.distance_to(left_mid),
            diameter_m=diameter_m,
            label="Left Diagonal Brace",
            description="Lateral bracing for wind resistance",
        ))

    if brace_count >= 2:
        # Right diagonal: from ~3/4 point on bottom to mid-height on right rafter
        qx = span_m * 0.75
        right_mid = Point3D(
            x=(P3.x + P2.x) / 2,
            y=(P3.y + P2.y) / 2,
            z=0,
        )
        brace_start_r = Point3D(x=qx, y=qy, z=0)
        truss.members.append(TrussMember(
            id="M-BRACE-R",
            member_type="brace",
            material_id=material_id,
            start=brace_start_r,
            end=right_mid,
            length_m=brace_start_r.distance_to(right_mid),
            diameter_m=diameter_m,
            label="Right Diagonal Brace",
            description="Lateral bracing for wind resistance",
        ))

    # --- Connections (joint nodes) ---
    truss.connections = [
        TrussConnection("J-P0", "M-BOTTOM", "M-LEFT-RAFTER", "bolted", P0),
        TrussConnection("J-P1", "M-BOTTOM", "M-KING-POST", "bolted", P1),
        TrussConnection("J-P2-LEFT", "M-LEFT-RAFTER", "M-KING-POST", "lashed", P2),
        TrussConnection("J-P2-RIGHT", "M-RIGHT-RAFTER", "M-KING-POST", "lashed", P2),
        TrussConnection("J-P3", "M-BOTTOM", "M-RIGHT-RAFTER", "bolted", P3),
    ]

    return truss


def build_full_shelter(
    span_m: float,
    height_m: float,
    material_id: str,
    diameter_m: float = 0.08,
    width_m: float = 5.0,
    brace_count: int = 2,
    wall_height_m: float = 2.4,
) -> TrussGeometry:
    """
    Build a complete shelter structure with two trusses (front + back),
    connecting purlins, and wall columns.

    Front truss at Z=0, back truss at Z=width_m.
    """
    front = build_simple_truss(span_m, height_m, material_id, diameter_m, width_m, brace_count)
    back = build_simple_truss(span_m, height_m, material_id, diameter_m, width_m, brace_count)

    # Offset back truss along Z
    for node_name, point in list(back.nodes.items()):
        back.nodes[node_name] = Point3D(x=point.x, y=point.y, z=width_m)

    # Rename back truss members
    for member in front.members:
        member.id = f"FRONT-{member.id}"
    for member in back.members:
        member.id = f"BACK-{member.id}"

    # Combine
    all_nodes = {}
    all_nodes.update(front.nodes)
    all_nodes.update(back.nodes)

    all_members = front.members + back.members
    all_connections = front.connections + back.connections

    # Add purlins (ridge beam connecting front peak to back peak)
    front_peak = Point3D(x=span_m / 2, y=height_m, z=0)
    back_peak = Point3D(x=span_m / 2, y=height_m, z=width_m)
    all_members.append(TrussMember(
        id="M-RIDGE",
        member_type="beam",
        material_id=material_id,
        start=front_peak,
        end=back_peak,
        length_m=front_peak.distance_to(back_peak),
        diameter_m=diameter_m,
        label="Ridge Beam",
        description="Connects front and back truss peaks",
    ))

    # Add eave beams (bottom chord connectors)
    front_left = Point3D(x=0, y=0, z=0)
    back_left = Point3D(x=0, y=0, z=width_m)
    all_members.append(TrussMember(
        id="M-EAVE-L",
        member_type="beam",
        material_id=material_id,
        start=front_left,
        end=back_left,
        length_m=front_left.distance_to(back_left),
        diameter_m=diameter_m,
        label="Left Eave Beam",
        description="Left eave connecting front and back",
    ))

    front_right = Point3D(x=span_m, y=0, z=0)
    back_right = Point3D(x=span_m, y=0, z=width_m)
    all_members.append(TrussMember(
        id="M-EAVE-R",
        member_type="beam",
        material_id=material_id,
        start=front_right,
        end=back_right,
        length_m=front_right.distance_to(back_right),
        diameter_m=diameter_m,
        label="Right Eave Beam",
        description="Right eave connecting front and back",
    ))

    # Add wall columns (front and back)
    for z_pos, prefix in [(0, "FRONT"), (width_m, "BACK")]:
        all_members.append(TrussMember(
            id=f"M-{prefix}-COL-L",
            member_type="column",
            material_id=material_id,
            start=Point3D(x=0, y=0, z=z_pos),
            end=Point3D(x=0, y=wall_height_m, z=z_pos),
            length_m=wall_height_m,
            diameter_m=diameter_m,
            label=f"{prefix.title()} Left Column",
            description=f"Front left wall column, {wall_height_m}m",
        ))
        all_members.append(TrussMember(
            id=f"M-{prefix}-COL-R",
            member_type="column",
            material_id=material_id,
            start=Point3D(x=span_m, y=0, z=z_pos),
            end=Point3D(x=span_m, y=wall_height_m, z=z_pos),
            length_m=wall_height_m,
            diameter_m=diameter_m,
            label=f"{prefix.title()} Right Column",
            description=f"Front right wall column, {wall_height_m}m",
        ))

    truss = TrussGeometry(
        design_type="roof_truss",
        span_m=span_m,
        height_m=height_m,
        width_m=width_m,
        members=all_members,
        connections=all_connections,
        nodes=all_nodes,
    )

    return truss
