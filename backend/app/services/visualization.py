"""Data visualization service — chart configurations for frontend rendering.

Generates Chart.js, D3.js, and Recharts compatible chart configs.
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/charts", tags=["Data Visualization"])


# ── Chart Configurations ──────────────────────────────────────────────

class ChartConfig(BaseModel):
    chart_type: str
    title: str
    data: dict
    options: dict = {}


class VisualizationService:
    """Generate chart configurations for frontend rendering."""

    # Color palette matching PANAGAH theme
    COLORS = {
        "primary": "#2D6A4F",
        "secondary": "#40916C",
        "accent": "#D4A373",
        "light": "#CCD5AE",
        "bg": "#0C252A",
        "surface": "#FFFFFF",
        "success": "#2D6A4F",
        "warning": "#D4A373",
        "error": "#E63946",
        "info": "#457B9D",
    }

    PALETTE = ["#2D6A4F", "#40916C", "#D4A373", "#CCD5AE", "#457B9D",
               "#E63946", "#264653", "#2A9D8F", "#E9C46A", "#F4A261"]

    def validation_results_chart(self, passed: int, failed: int,
                                  warning: int, not_evaluated: int) -> ChartConfig:
        """Donut chart showing validation results distribution."""
        return ChartConfig(
            chart_type="doughnut",
            title="Validation Results Distribution",
            data={
                "labels": ["Passed", "Failed", "Warning", "Not Evaluated"],
                "datasets": [{
                    "data": [passed, failed, warning, not_evaluated],
                    "backgroundColor": [
                        self.COLORS["success"], self.COLORS["error"],
                        self.COLORS["warning"], "#95A5A6"
                    ],
                    "borderWidth": 2,
                    "borderColor": self.COLORS["surface"],
                }],
            },
            options={
                "cutout": "60%",
                "plugins": {
                    "legend": {"position": "bottom"},
                    "title": {"display": True, "text": "Validation Results"},
                },
            },
        )

    def cost_breakdown_chart(self, categories: dict[str, float]) -> ChartConfig:
        """Bar chart showing cost breakdown by category."""
        labels = list(categories.keys())
        values = list(categories.values())

        return ChartConfig(
            chart_type="bar",
            title="Cost Breakdown by Category",
            data={
                "labels": labels,
                "datasets": [{
                    "label": "Cost (USD)",
                    "data": values,
                    "backgroundColor": self.PALETTE[:len(labels)],
                    "borderRadius": 8,
                    "borderSkipped": False,
                }],
            },
            options={
                "responsive": True,
                "plugins": {
                    "legend": {"display": False},
                    "title": {"display": True, "text": "Cost Breakdown"},
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "USD"}},
                },
            },
        )

    def material_distribution_chart(self, materials: dict[str, float]) -> ChartConfig:
        """Pie chart showing material distribution."""
        labels = list(materials.keys())
        values = list(materials.values())

        return ChartConfig(
            chart_type="pie",
            title="Material Distribution",
            data={
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": self.PALETTE[:len(labels)],
                    "borderWidth": 2,
                    "borderColor": self.COLORS["surface"],
                }],
            },
            options={
                "plugins": {
                    "legend": {"position": "right"},
                    "title": {"display": True, "text": "Material Distribution"},
                },
            },
        )

    def design_comparison_radar(self, designs: list[dict]) -> ChartConfig:
        """Radar chart comparing multiple designs across criteria."""
        criteria = ["Structural", "Cost", "Compliance", "Availability", "Complexity"]
        datasets = []

        for i, design in enumerate(designs):
            datasets.append({
                "label": design.get("name", f"Design {i+1}"),
                "data": [
                    design.get("structural_score", 50),
                    design.get("cost_score", 50),
                    design.get("compliance_score", 50),
                    design.get("availability_score", 50),
                    design.get("complexity_score", 50),
                ],
                "backgroundColor": f"rgba(45, 106, 79, 0.2)",
                "borderColor": self.PALETTE[i % len(self.PALETTE)],
                "pointBackgroundColor": self.PALETTE[i % len(self.PALETTE)],
                "borderWidth": 2,
            })

        return ChartConfig(
            chart_type="radar",
            title="Design Comparison",
            data={
                "labels": criteria,
                "datasets": datasets,
            },
            options={
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "max": 100,
                        "ticks": {"stepSize": 20},
                    }
                },
                "plugins": {
                    "title": {"display": True, "text": "Design Comparison Matrix"},
                },
            },
        )

    def project_timeline_chart(self, events: list[dict]) -> ChartConfig:
        """Line chart showing project activity over time."""
        dates = [e.get("date", "") for e in events]
        counts = [e.get("count", 0) for e in events]

        return ChartConfig(
            chart_type="line",
            title="Project Activity Timeline",
            data={
                "labels": dates,
                "datasets": [{
                    "label": "Events",
                    "data": counts,
                    "borderColor": self.COLORS["primary"],
                    "backgroundColor": "rgba(45, 106, 79, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                    "pointRadius": 4,
                    "pointHoverRadius": 6,
                }],
            },
            options={
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Activity Timeline"},
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Events"}},
                },
            },
        )

    def wind_load_chart(self, zones: list[dict]) -> ChartConfig:
        """Bar chart showing wind pressure by zone."""
        labels = [z.get("zone", f"Zone {i}") for i, z in enumerate(zones)]
        values = [z.get("pressure_kpa", 0) for z in zones]

        return ChartConfig(
            chart_type="bar",
            title="Wind Pressure by Zone (ASCE 7-22)",
            data={
                "labels": labels,
                "datasets": [{
                    "label": "Pressure (kPa)",
                    "data": values,
                    "backgroundColor": self.PALETTE[:len(labels)],
                    "borderRadius": 6,
                }],
            },
            options={
                "indexAxis": "y",
                "plugins": {
                    "title": {"display": True, "text": "Wind Pressure Distribution"},
                },
                "scales": {
                    "x": {"beginAtZero": True, "title": {"display": True, "text": "kPa"}},
                },
            },
        )

    def safety_factors_chart(self, members: list[dict]) -> ChartConfig:
        """Horizontal bar chart showing safety factors per member."""
        labels = [m.get("name", f"Member {i}") for i, m in enumerate(members)]
        values = [m.get("safety_factor", 1.0) for m in members]
        colors = [
            self.COLORS["error"] if v < 1.0 else
            self.COLORS["warning"] if v < 1.5 else
            self.COLORS["success"]
            for v in values
        ]

        return ChartConfig(
            chart_type="bar",
            title="Member Safety Factors",
            data={
                "labels": labels,
                "datasets": [{
                    "label": "Safety Factor",
                    "data": values,
                    "backgroundColor": colors,
                    "borderRadius": 4,
                }],
            },
            options={
                "indexAxis": "y",
                "plugins": {
                    "title": {"display": True, "text": "Structural Safety Factors"},
                    "annotation": {
                        "annotations": {
                            "minLine": {
                                "type": "line",
                                "xMin": 1.5,
                                "xMax": 1.5,
                                "borderColor": self.COLORS["error"],
                                "borderWidth": 2,
                                "borderDash": [5, 5],
                                "label": {"content": "Min Required", "enabled": True},
                            }
                        }
                    },
                },
                "scales": {
                    "x": {"beginAtZero": True, "title": {"display": True, "text": "Safety Factor"}},
                },
            },
        )

    def seismic_load_chart(self, story_forces: list[dict]) -> ChartConfig:
        """Bar chart showing seismic forces per story."""
        labels = [f"Story {s.get('level', i+1)}" for i, s in enumerate(story_forces)]
        forces = [s.get("force_kn", 0) for s in story_forces]

        return ChartConfig(
            chart_type="bar",
            title="Seismic Force Distribution (ELF)",
            data={
                "labels": labels,
                "datasets": [{
                    "label": "Lateral Force (kN)",
                    "data": forces,
                    "backgroundColor": self.COLORS["info"],
                    "borderRadius": 6,
                }],
            },
            options={
                "plugins": {
                    "title": {"display": True, "text": "Seismic Force Distribution"},
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Force (kN)"}},
                },
            },
        )

    def dashboard_summary(self, stats: dict) -> list[ChartConfig]:
        """Generate multiple charts for dashboard overview."""
        charts = []

        # Project status donut
        if "projects_by_status" in stats:
            charts.append(self.validation_results_chart(
                passed=stats["projects_by_status"].get("active", 0),
                failed=stats["projects_by_status"].get("archived", 0),
                warning=stats["projects_by_status"].get("draft", 0),
                not_evaluated=0,
            ))

        # Cost breakdown bar
        if "cost_breakdown" in stats:
            charts.append(self.cost_breakdown_chart(stats["cost_breakdown"]))

        # Material distribution pie
        if "material_usage" in stats:
            charts.append(self.material_distribution_chart(stats["material_usage"]))

        # Activity timeline
        if "activity_timeline" in stats:
            charts.append(self.project_timeline_chart(stats["activity_timeline"]))

        return charts


viz_service = VisualizationService()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.get("/validation-results", summary="Validation results chart")
async def validation_chart(
    passed: int = Query(0), failed: int = Query(0),
    warning: int = Query(0), not_evaluated: int = Query(0),
):
    """Donut chart of validation results distribution."""
    return viz_service.validation_results_chart(passed, failed, warning, not_evaluated).model_dump()


@router.get("/cost-breakdown", summary="Cost breakdown chart")
async def cost_chart(categories: str = Query("materials:5000,labor:3000,transport:1000")):
    """Bar chart of cost breakdown. Pass as key:value pairs."""
    cat_dict = {}
    for pair in categories.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            cat_dict[k.strip()] = float(v.strip())
    return viz_service.cost_breakdown_chart(cat_dict).model_dump()


@router.get("/material-distribution", summary="Material distribution chart")
async def material_chart(materials: str = Query("bamboo:40,earth:30,metal:20,other:10")):
    """Pie chart of material distribution."""
    mat_dict = {}
    for pair in materials.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            mat_dict[k.strip()] = float(v.strip())
    return viz_service.material_distribution_chart(mat_dict).model_dump()


@router.post("/design-comparison", summary="Design comparison radar chart")
async def comparison_chart(designs: list[dict]):
    """Radar chart comparing multiple designs."""
    return viz_service.design_comparison_radar(designs).model_dump()


@router.get("/timeline", summary="Activity timeline chart")
async def timeline_chart(days: int = Query(30, ge=1, le=365)):
    """Line chart of project activity over time."""
    import random
    from datetime import datetime, timedelta

    events = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        events.append({"date": date, "count": random.randint(0, 10)})

    return viz_service.project_timeline_chart(events).model_dump()


@router.get("/wind-load", summary="Wind load chart")
async def wind_chart():
    """Horizontal bar chart of wind pressure by zone."""
    zones = [
        {"zone": "Zone A (Corner)", "pressure_kpa": 1.2},
        {"zone": "Zone B (Edge)", "pressure_kpa": 0.9},
        {"zone": "Zone C (Interior)", "pressure_kpa": 0.7},
        {"zone": "Zone D (Corner)", "pressure_kpa": 1.4},
        {"zone": "Zone E (Edge)", "pressure_kpa": 1.0},
        {"zone": "Zone F (Interior)", "pressure_kpa": 0.8},
    ]
    return viz_service.wind_load_chart(zones).model_dump()


@router.get("/safety-factors", summary="Safety factors chart")
async def safety_chart():
    """Horizontal bar chart of member safety factors."""
    members = [
        {"name": "King Post", "safety_factor": 2.1},
        {"name": "Left Rafter", "safety_factor": 1.8},
        {"name": "Right Rafter", "safety_factor": 1.7},
        {"name": "Bottom Chord", "safety_factor": 1.5},
        {"name": "Diagonal Brace", "safety_factor": 1.3},
        {"name": "Wall Column", "safety_factor": 2.5},
    ]
    return viz_service.safety_factors_chart(members).model_dump()


@router.post("/dashboard", summary="Generate all dashboard charts")
async def dashboard_charts(stats: dict):
    """Generate all charts needed for the dashboard overview."""
    charts = viz_service.dashboard_summary(stats)
    return {
        "total_charts": len(charts),
        "charts": [c.model_dump() for c in charts],
    }


@router.get("/recharts/{chart_type}", summary="Recharts-compatible format")
async def recharts_format(
    chart_type: str,
    data: str = Query("label1:10,label2:20,label3:30"),
):
    """
    Get data in Recharts-compatible format (React frontend).

    Supports: bar, line, pie, radar
    """
    data_dict = {}
    for pair in data.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            data_dict[k.strip()] = float(v.strip())

    recharts_data = [{"name": k, "value": v} for k, v in data_dict.items()]

    return {
        "chart_type": chart_type,
        "data": recharts_data,
        "recharts_component": {
            "bar": "BarChart",
            "line": "LineChart",
            "pie": "PieChart",
            "radar": "RadarChart",
        }.get(chart_type, "BarChart"),
    }
