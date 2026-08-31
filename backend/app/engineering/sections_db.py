"""Standard Member Sections Database — AISC Steel Shapes.

Complete AISC W-shape, HSS, channel, and angle sections with full properties.
Properties in metric (SI) units converted from AISC Imperial.

Includes:
- W-shapes (wide flange beams/columns)
- HSS (hollow structural sections — rectangular and square)
- C-channels
- L-angles
- Round HSS

All properties per AISC 15th Edition Manual.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SectionType(str, Enum):
    W_SHAPE = "W"
    HSS_RECT = "HSS-R"
    HSS_SQ = "HSS-S"
    HSS_ROUND = "HSS-RO"
    CHANNEL = "C"
    ANGLE = "L"
    PIPE = "Pipe"


@dataclass(frozen=True)
class AISCSection:
    """AISC section with full structural properties."""
    designation: str
    section_type: SectionType
    # Geometric properties (SI)
    depth: float          # m (section depth)
    width: float          # m (flange width or outer dimension)
    tw: float             # m (web thickness)
    tf: float             # m (flange thickness)
    A: float              # m² (cross-sectional area)
    Ix: float             # m⁴ (moment of inertia, strong axis)
    Iy: float             # m⁴ (moment of inertia, weak axis)
    Zx: float             # m³ (plastic section modulus, strong axis)
    Zy: float             # m³ (plastic section modulus, weak axis)
    Sx: float             # m³ (elastic section modulus, strong axis)
    Sy: float             # m³ (elastic section modulus, weak axis)
    rx: float             # m (radius of gyration, strong axis)
    ry: float             # m (radius of gyration, weak axis)
    J: float              # m⁴ (torsion constant)
    Cw: float             # m⁶ (warping constant)
    weight_per_length: float  # kg/m

    # Compactness
    bf_2tf: float = 0.0   # flange width / thickness ratio
    h_tw: float = 0.0     # web height / thickness ratio


# ── Conversion helpers ──────────────────────────────────────────────

def _in_to_m(val: float) -> float:
    return val * 0.0254

def _in2_to_m2(val: float) -> float:
    return val * (0.0254 ** 2)

def _in4_to_m4(val: float) -> float:
    return val * (0.0254 ** 4)

def _in3_to_m3(val: float) -> float:
    return val * (0.0254 ** 3)

def _in_to_m_single(val: float) -> float:
    return val * 0.0254

def _lb_ft_to_kg_m(val: float) -> float:
    return val * 1.4882


# ── AISC W-Shape Database ──────────────────────────────────────────

AISC_W_SHAPES: list[AISCSection] = [
    # W6x15
    AISCSection(
        designation="W6×15", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(6.38), width=_in_to_m(6.00),
        tw=_in_to_m(0.260), tf=_in_to_m(0.430),
        A=_in2_to_m2(4.43), Ix=_in4_to_m4(29.1), Iy=_in4_to_m4(9.32),
        Zx=_in3_to_m3(10.7), Zy=_in3_to_m3(4.65),
        Sx=_in3_to_m3(9.11), Sy=_in3_to_m3(3.10),
        rx=_in_to_m_single(2.56), ry=_in_to_m_single(1.46),
        J=_in4_to_m4(0.224), Cw=_in4_to_m4(67.6) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(15),
        bf_2tf=6.98, h_tw=17.3,
    ),
    # W8x10
    AISCSection(
        designation="W8×10", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(7.89), width=_in_to_m(3.94),
        tw=_in_to_m(0.170), tf=_in_to_m(0.205),
        A=_in2_to_m2(2.96), Ix=_in4_to_m4(30.8), Iy=_in4_to_m4(2.09),
        Zx=_in3_to_m3(8.87), Zy=_in3_to_m3(1.52),
        Sx=_in3_to_m3(7.81), Sy=_in3_to_m3(1.06),
        rx=_in_to_m_single(3.22), ry=_in_to_m_single(0.841),
        J=_in4_to_m4(0.0342), Cw=_in4_to_m4(14.2) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(10),
        bf_2tf=9.61, h_tw=41.3,
    ),
    # W8x31
    AISCSection(
        designation="W8×31", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(8.00), width=_in_to_m(8.00),
        tw=_in_to_m(0.285), tf=_in_to_m(0.435),
        A=_in2_to_m2(9.13), Ix=_in4_to_m4(110), Iy=_in4_to_m4(37.1),
        Zx=_in3_to_m3(30.4), Zy=_in3_to_m3(13.7),
        Sx=_in3_to_m3(27.5), Sy=_in3_to_m3(9.27),
        rx=_in_to_m_single(3.47), ry=_in_to_m_single(2.02),
        J=_in4_to_m4(0.875), Cw=_in4_to_m4(269) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(31),
        bf_2tf=9.20, h_tw=22.6,
    ),
    # W10×12
    AISCSection(
        designation="W10×12", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(9.87), width=_in_to_m(3.96),
        tw=_in_to_m(0.190), tf=_in_to_m(0.210),
        A=_in2_to_m2(3.54), Ix=_in4_to_m4(53.8), Iy=_in4_to_m4(2.18),
        Zx=_in3_to_m3(12.6), Zy=_in3_to_m3(1.62),
        Sx=_in3_to_m3(10.9), Sy=_in3_to_m3(1.10),
        rx=_in_to_m_single(3.90), ry=_in_to_m_single(0.785),
        J=_in4_to_m4(0.0614), Cw=_in4_to_m4(22.8) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(12),
        bf_2tf=9.43, h_tw=47.0,
    ),
    # W10×45
    AISCSection(
        designation="W10×45", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(10.1), width=_in_to_m(8.02),
        tw=_in_to_m(0.350), tf=_in_to_m(0.620),
        A=_in2_to_m2(13.3), Ix=_in4_to_m4(248), Iy=_in4_to_m4(53),
        Zx=_in3_to_m3(54.9), Zy=_in3_to_m3(18.9),
        Sx=_in3_to_m3(49.1), Sy=_in3_to_m3(9.27),
        rx=_in_to_m_single(4.32), ry=_in_to_m_single(2.01),
        J=_in4_to_m4(2.66), Cw=_in4_to_m4(678) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(45),
        bf_2tf=6.47, h_tw=23.8,
    ),
    # W12×16
    AISCSection(
        designation="W12×16", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(11.99), width=_in_to_m(3.99),
        tw=_in_to_m(0.220), tf=_in_to_m(0.265),
        A=_in2_to_m2(4.71), Ix=_in4_to_m4(103), Iy=_in4_to_m4(2.82),
        Zx=_in3_to_m3(19.2), Zy=_in3_to_m3(2.12),
        Sx=_in3_to_m3(17.1), Sy=_in3_to_m3(1.41),
        rx=_in_to_m_single(4.67), ry=_in_to_m_single(0.773),
        J=_in4_to_m4(0.103), Cw=_in4_to_m4(25.7) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(16),
        bf_2tf=7.53, h_tw=49.4,
    ),
    # W12×30
    AISCSection(
        designation="W12×30", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(12.3), width=_in_to_m(6.52),
        tw=_in_to_m(0.260), tf=_in_to_m(0.440),
        A=_in2_to_m2(8.79), Ix=_in4_to_m4(238), Iy=_in4_to_m4(20.3),
        Zx=_in3_to_m3(43.1), Zy=_in3_to_m3(9.33),
        Sx=_in3_to_m3(38.6), Sy=_in3_to_m3(6.24),
        rx=_in_to_m_single(5.21), ry=_in_to_m_single(1.52),
        J=_in4_to_m4(0.846), Cw=_in4_to_m4(196) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(30),
        bf_2tf=7.41, h_tw=43.1,
    ),
    # W12×50
    AISCSection(
        designation="W12×50", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(12.2), width=_in_to_m(8.08),
        tw=_in_to_m(0.370), tf=_in_to_m(0.640),
        A=_in2_to_m2(14.6), Ix=_in4_to_m4(391), Iy=_in4_to_m4(56.3),
        Zx=_in3_to_m3(71.9), Zy=_in3_to_m3(20.7),
        Sx=_in3_to_m3(64.2), Sy=_in3_to_m3(13.9),
        rx=_in_to_m_single(5.18), ry=_in_to_m_single(1.96),
        J=_in4_to_m4(3.74), Cw=_in4_to_m4(648) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(50),
        bf_2tf=6.31, h_tw=28.5,
    ),
    # W14×22
    AISCSection(
        designation="W14×22", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(13.7), width=_in_to_m(5.00),
        tw=_in_to_m(0.230), tf=_in_to_m(0.335),
        A=_in2_to_m2(6.49), Ix=_in4_to_m4(199), Iy=_in4_to_m4(7.00),
        Zx=_in3_to_m3(33.2), Zy=_in3_to_m3(4.20),
        Sx=_in3_to_m3(29.0), Sy=_in3_to_m3(2.80),
        rx=_in_to_m_single(5.54), ry=_in_to_m_single(1.04),
        J=_in4_to_m4(0.237), Cw=_in4_to_m4(61.1) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(22),
        bf_2tf=7.46, h_tw=54.0,
    ),
    # W14×43
    AISCSection(
        designation="W14×43", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(13.7), width=_in_to_m(8.00),
        tw=_in_to_m(0.305), tf=_in_to_m(0.530),
        A=_in2_to_m2(12.6), Ix=_in4_to_m4(428), Iy=_in4_to_m4(45.2),
        Zx=_in3_to_m3(69.6), Zy=_in3_to_m3(16.8),
        Sx=_in3_to_m3(62.7), Sy=_in3_to_m3(11.3),
        rx=_in_to_m_single(5.82), ry=_in_to_m_single(1.89),
        J=_in4_to_m4(1.90), Cw=_in4_to_m4(490) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(43),
        bf_2tf=7.55, h_tw=38.7,
    ),
    # W14×61
    AISCSection(
        designation="W14×61", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(13.9), width=_in_to_m(10.0),
        tw=_in_to_m(0.375), tf=_in_to_m(0.645),
        A=_in2_to_m2(18.0), Ix=_in4_to_m4(640), Iy=_in4_to_m4(107),
        Zx=_in3_to_m3(102), Zy=_in3_to_m3(31.8),
        Sx=_in3_to_m3(92.1), Sy=_in3_to_m3(21.2),
        rx=_in_to_m_single(5.98), ry=_in_to_m_single(2.45),
        J=_in4_to_m4(4.70), Cw=_in4_to_m4(1550) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(61),
        bf_2tf=7.75, h_tw=32.2,
    ),
    # W16×31
    AISCSection(
        designation="W16×31", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(15.9), width=_in_to_m(5.53),
        tw=_in_to_m(0.275), tf=_in_to_m(0.440),
        A=_in2_to_m2(9.12), Ix=_in4_to_m4(375), Iy=_in4_to_m4(12.1),
        Zx=_in3_to_m3(53.0), Zy=_in3_to_m3(6.77),
        Sx=_in3_to_m3(47.2), Sy=_in3_to_m3(4.39),
        rx=_in_to_m_single(6.40), ry=_in_to_m_single(1.15),
        J=_in4_to_m4(0.561), Cw=_in4_to_m4(127) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(31),
        bf_2tf=6.28, h_tw=51.4,
    ),
    # W18×35
    AISCSection(
        designation="W18×35", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(17.7), width=_in_to_m(6.00),
        tw=_in_to_m(0.300), tf=_in_to_m(0.425),
        A=_in2_to_m2(10.3), Ix=_in4_to_m4(510), Iy=_in4_to_m4(15.3),
        Zx=_in3_to_m3(66.5), Zy=_in3_to_m3(7.83),
        Sx=_in3_to_m3(57.6), Sy=_in3_to_m3(5.09),
        rx=_in_to_m_single(7.04), ry=_in_to_m_single(1.22),
        J=_in4_to_m4(0.758), Cw=_in4_to_m4(178) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(35),
        bf_2tf=7.06, h_tw=53.0,
    ),
    # W18×50
    AISCSection(
        designation="W18×50", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(18.0), width=_in_to_m(7.50),
        tw=_in_to_m(0.355), tf=_in_to_m(0.570),
        A=_in2_to_m2(14.7), Ix=_in4_to_m4(800), Iy=_in4_to_m4(40.1),
        Zx=_in3_to_m3(101), Zy=_in3_to_m3(15.8),
        Sx=_in3_to_m3(88.9), Sy=_in3_to_m3(10.7),
        rx=_in_to_m_single(7.36), ry=_in_to_m_single(1.65),
        J=_in4_to_m4(2.44), Cw=_in4_to_m4(490) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(50),
        bf_2tf=6.58, h_tw=44.5,
    ),
    # W21×44
    AISCSection(
        designation="W21×44", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(20.7), width=_in_to_m(6.50),
        tw=_in_to_m(0.350), tf=_in_to_m(0.450),
        A=_in2_to_m2(13.0), Ix=_in4_to_m4(843), Iy=_in4_to_m4(20.7),
        Zx=_in3_to_m3(95.4), Zy=_in3_to_m3(9.54),
        Sx=_in3_to_m3(81.6), Sy=_in3_to_m3(6.39),
        rx=_in_to_m_single(8.06), ry=_in_to_m_single(1.26),
        J=_in4_to_m4(1.14), Cw=_in4_to_m4(278) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(44),
        bf_2tf=7.22, h_tw=53.7,
    ),
    # W24×55
    AISCSection(
        designation="W24×55", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(23.6), width=_in_to_m(7.01),
        tw=_in_to_m(0.395), tf=_in_to_m(0.505),
        A=_in2_to_m2(16.3), Ix=_in4_to_m4(1350), Iy=_in4_to_m4(29.1),
        Zx=_in3_to_m3(134), Zy=_in3_to_m3(12.3),
        Sx=_in3_to_m3(114), Sy=_in3_to_m3(8.31),
        rx=_in_to_m_single(9.11), ry=_in_to_m_single(1.34),
        J=_in4_to_m4(2.13), Cw=_in4_to_m4(461) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(55),
        bf_2tf=6.94, h_tw=52.6,
    ),
    # W24×76
    AISCSection(
        designation="W24×76", section_type=SectionType.W_SHAPE,
        depth=_in_to_m(23.9), width=_in_to_m(9.00),
        tw=_in_to_m(0.440), tf=_in_to_m(0.680),
        A=_in2_to_m2(22.4), Ix=_in4_to_m4(2100), Iy=_in4_to_m4(94.4),
        Zx=_in3_to_m3(199), Zy=_in3_to_m3(31.4),
        Sx=_in3_to_m3(176), Sy=_in3_to_m3(21.0),
        rx=_in_to_m_single(9.69), ry=_in_to_m_single(2.06),
        J=_in4_to_m4(6.63), Cw=_in4_to_m4(1720) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(76),
        bf_2tf=6.62, h_tw=46.0,
    ),
]


# ── HSS (Rectangular/Square) ───────────────────────────────────────

AISC_HSS_SHAPES: list[AISCSection] = [
    # HSS4x4x1/4
    AISCSection(
        designation="HSS4×4×¼", section_type=SectionType.HSS_SQ,
        depth=_in_to_m(4.00), width=_in_to_m(4.00),
        tw=_in_to_m(0.233), tf=_in_to_m(0.233),
        A=_in2_to_m2(3.37), Ix=_in4_to_m4(7.80), Iy=_in4_to_m4(7.80),
        Zx=_in3_to_m3(4.63), Zy=_in3_to_m3(4.63),
        Sx=_in3_to_m3(3.90), Sy=_in3_to_m3(3.90),
        rx=_in_to_m_single(1.52), ry=_in_to_m_single(1.52),
        J=_in4_to_m4(12.3), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(9.97),
    ),
    # HSS6x6x3/8
    AISCSection(
        designation="HSS6×6×⅜", section_type=SectionType.HSS_SQ,
        depth=_in_to_m(6.00), width=_in_to_m(6.00),
        tw=_in_to_m(0.349), tf=_in_to_m(0.349),
        A=_in2_to_m2(7.58), Ix=_in4_to_m4(39.4), Iy=_in4_to_m4(39.4),
        Zx=_in3_to_m3(16.4), Zy=_in3_to_m3(16.4),
        Sx=_in3_to_m3(13.1), Sy=_in3_to_m3(13.1),
        rx=_in_to_m_single(2.28), ry=_in_to_m_single(2.28),
        J=_in4_to_m4(62.2), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(22.6),
    ),
    # HSS8x8x1/2
    AISCSection(
        designation="HSS8×8×½", section_type=SectionType.HSS_SQ,
        depth=_in_to_m(8.00), width=_in_to_m(8.00),
        tw=_in_to_m(0.465), tf=_in_to_m(0.465),
        A=_in2_to_m2(13.5), Ix=_in4_to_m4(146), Iy=_in4_to_m4(146),
        Zx=_in3_to_m3(43.9), Zy=_in3_to_m3(43.9),
        Sx=_in3_to_m3(36.5), Sy=_in3_to_m3(36.5),
        rx=_in_to_m_single(3.28), ry=_in_to_m_single(3.28),
        J=_in4_to_m4(252), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(40.8),
    ),
    # HSS10x10x1/2
    AISCSection(
        designation="HSS10×10×½", section_type=SectionType.HSS_SQ,
        depth=_in_to_m(10.0), width=_in_to_m(10.0),
        tw=_in_to_m(0.465), tf=_in_to_m(0.465),
        A=_in2_to_m2(17.2), Ix=_in4_to_m4(300), Iy=_in4_to_m4(300),
        Zx=_in3_to_m3(72.1), Zy=_in3_to_m3(72.1),
        Sx=_in3_to_m3(60.0), Sy=_in3_to_m3(60.0),
        rx=_in_to_m_single(4.18), ry=_in_to_m_single(4.18),
        J=_in4_to_m4(493), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(51.9),
    ),
    # HSS12x12x5/8
    AISCSection(
        designation="HSS12×12×⅝", section_type=SectionType.HSS_SQ,
        depth=_in_to_m(12.0), width=_in_to_m(12.0),
        tw=_in_to_m(0.581), tf=_in_to_m(0.581),
        A=_in2_to_m2(26.2), Ix=_in4_to_m4(782), Iy=_in4_to_m4(782),
        Zx=_in3_to_m3(156), Zy=_in3_to_m3(156),
        Sx=_in3_to_m3(130), Sy=_in3_to_m3(130),
        rx=_in_to_m_single(5.46), ry=_in_to_m_single(5.46),
        J=_in4_to_m4(1280), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(79.4),
    ),
    # HSS6x4x3/8 (Rectangular)
    AISCSection(
        designation="HSS6×4×⅜", section_type=SectionType.HSS_RECT,
        depth=_in_to_m(6.00), width=_in_to_m(4.00),
        tw=_in_to_m(0.349), tf=_in_to_m(0.349),
        A=_in2_to_m2(6.02), Ix=_in4_to_m4(23.8), Iy=_in4_to_m4(13.4),
        Zx=_in3_to_m3(10.9), Zy=_in3_to_m3(8.06),
        Sx=_in3_to_m3(7.94), Sy=_in3_to_m3(5.36),
        rx=_in_to_m_single(1.99), ry=_in_to_m_single(1.49),
        J=_in4_to_m4(34.4), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(18.0),
    ),
    # HSS8x6x1/2
    AISCSection(
        designation="HSS8×6×½", section_type=SectionType.HSS_RECT,
        depth=_in_to_m(8.00), width=_in_to_m(6.00),
        tw=_in_to_m(0.465), tf=_in_to_m(0.465),
        A=_in2_to_m2(12.0), Ix=_in4_to_m4(106), Iy=_in4_to_m4(60.1),
        Zx=_in3_to_m3(34.4), Zy=_in3_to_m3(24.1),
        Sx=_in3_to_m3(26.5), Sy=_in3_to_m3(17.2),
        rx=_in_to_m_single(2.97), ry=_in_to_m_single(2.24),
        J=_in4_to_m4(151), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(36.3),
    ),
    # HSS10x6x5/8
    AISCSection(
        designation="HSS10×6×⅝", section_type=SectionType.HSS_RECT,
        depth=_in_to_m(10.0), width=_in_to_m(6.00),
        tw=_in_to_m(0.581), tf=_in_to_m(0.581),
        A=_in2_to_m2(17.2), Ix=_in4_to_m4(249), Iy=_in4_to_m4(76.6),
        Zx=_in3_to_m3(60.8), Zy=_in3_to_m3(32.3),
        Sx=_in3_to_m3(49.8), Sy=_in3_to_m3(23.0),
        rx=_in_to_m_single(3.81), ry=_in_to_m_single(2.11),
        J=_in4_to_m4(280), Cw=0.0,
        weight_per_length=_lb_ft_to_kg_m(52.1),
    ),
]


# ── Channel Shapes ─────────────────────────────────────────────────

AISC_CHANNEL_SHAPES: list[AISCSection] = [
    # C6x8.2
    AISCSection(
        designation="C6×8.2", section_type=SectionType.CHANNEL,
        depth=_in_to_m(6.00), width=_in_to_m(2.16),
        tw=_in_to_m(0.343), tf=_in_to_m(0.314),
        A=_in2_to_m2(2.40), Ix=_in4_to_m4(13.1), Iy=_in4_to_m4(0.692),
        Zx=_in3_to_m3(5.07), Zy=_in3_to_m3(0.621),
        Sx=_in3_to_m3(4.38), Sy=_in3_to_m3(0.385),
        rx=_in_to_m_single(2.34), ry=_in_to_m_single(0.536),
        J=_in4_to_m4(0.120), Cw=_in4_to_m4(2.13) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(8.2),
    ),
    # C8x11.5
    AISCSection(
        designation="C8×11.5", section_type=SectionType.CHANNEL,
        depth=_in_to_m(8.00), width=_in_to_m(2.26),
        tw=_in_to_m(0.220), tf=_in_to_m(0.311),
        A=_in2_to_m2(3.37), Ix=_in4_to_m4(32.6), Iy=_in4_to_m4(1.32),
        Zx=_in3_to_m3(9.67), Zy=_in3_to_m3(0.917),
        Sx=_in3_to_m3(8.14), Sy=_in3_to_m3(0.580),
        rx=_in_to_m_single(3.11), ry=_in_to_m_single(0.625),
        J=_in4_to_m4(0.125), Cw=_in4_to_m4(4.63) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(11.5),
    ),
    # C10x15.3
    AISCSection(
        designation="C10×15.3", section_type=SectionType.CHANNEL,
        depth=_in_to_m(10.0), width=_in_to_m(2.60),
        tw=_in_to_m(0.240), tf=_in_to_m(0.436),
        A=_in2_to_m2(4.48), Ix=_in4_to_m4(67.3), Iy=_in4_to_m4(2.27),
        Zx=_in3_to_m3(15.5), Zy=_in3_to_m3(1.65),
        Sx=_in3_to_m3(13.5), Sy=_in3_to_m3(1.03),
        rx=_in_to_m_single(3.87), ry=_in_to_m_single(0.714),
        J=_in4_to_m4(0.306), Cw=_in4_to_m4(10.6) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(15.3),
    ),
    # C12x20.7
    AISCSection(
        designation="C12×20.7", section_type=SectionType.CHANNEL,
        depth=_in_to_m(12.0), width=_in_to_m(2.94),
        tw=_in_to_m(0.282), tf=_in_to_m(0.501),
        A=_in2_to_m2(6.08), Ix=_in4_to_m4(129), Iy=_in4_to_m4(3.88),
        Zx=_in3_to_m3(24.8), Zy=_in3_to_m3(2.61),
        Sx=_in3_to_m3(21.5), Sy=_in3_to_m3(1.64),
        rx=_in_to_m_single(4.61), ry=_in_to_m_single(0.799),
        J=_in4_to_m4(0.684), Cw=_in4_to_m4(20.7) * (0.0254**2),
        weight_per_length=_lb_ft_to_kg_m(20.7),
    ),
]


# ── Lookup Functions ────────────────────────────────────────────────

_ALL_SECTIONS = AISC_W_SHAPES + AISC_HSS_SHAPES + AISC_CHANNEL_SHAPES

_SECTION_BY_DESIGNATION: dict[str, AISCSection] = {
    s.designation: s for s in _ALL_SECTIONS
}

_SECTIONS_BY_TYPE: dict[SectionType, list[AISCSection]] = {}
for s in _ALL_SECTIONS:
    _SECTIONS_BY_TYPE.setdefault(s.section_type, []).append(s)


def get_section(designation: str) -> Optional[AISCSection]:
    """Look up a section by designation (e.g., 'W12×50')."""
    return _SECTION_BY_DESIGNATION.get(designation)


def get_sections_by_type(section_type: SectionType) -> list[AISCSection]:
    """Get all sections of a given type."""
    return _SECTIONS_BY_TYPE.get(section_type, [])


def get_w_shapes() -> list[AISCSection]:
    """Get all W-shape sections."""
    return AISC_W_SHAPES[:]


def get_hss_shapes() -> list[AISCSection]:
    """Get all HSS sections."""
    return AISC_HSS_SHAPES[:]


def get_channel_shapes() -> list[AISCSection]:
    """Get all channel sections."""
    return AISC_CHANNEL_SHAPES[:]


def find_sections_min_Ix(min_Ix: float) -> list[AISCSection]:
    """Find all sections with Ix >= min_Ix (m⁴), sorted by weight."""
    return sorted(
        [s for s in _ALL_SECTIONS if s.Ix >= min_Ix],
        key=lambda s: s.weight_per_length,
    )


def find_sections_min_Zx(min_Zx: float) -> list[AISCSection]:
    """Find all sections with Zx >= min_Zx (m³), sorted by weight."""
    return sorted(
        [s for s in _ALL_SECTIONS if s.Zx >= min_Zx],
        key=lambda s: s.weight_per_length,
    )


def find_sections_in_range(
    depth_min: float = 0,
    depth_max: float = float('inf'),
    weight_min: float = 0,
    weight_max: float = float('inf'),
) -> list[AISCSection]:
    """Find sections within depth and weight ranges."""
    return [
        s for s in _ALL_SECTIONS
        if depth_min <= s.depth <= depth_max
        and weight_min <= s.weight_per_length <= weight_max
    ]


def list_all_designations() -> list[str]:
    """List all available section designations."""
    return sorted(_SECTION_BY_DESIGNATION.keys())
