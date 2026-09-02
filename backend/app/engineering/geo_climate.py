"""
Geo-Climate Lookup Service

Provides:
  - Climate zone classification from coordinates
  - Wind zone mapping for any location
  - Seismic zone mapping
  - Recommended materials by climate
  - Construction season recommendations

Based on:
  - ASCE 7-22 wind speed maps
  - IS 1893 seismic zone maps
  - Koppen climate classification (simplified)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ClimateZone:
    """Climate information for a geographic location."""
    zone_name: str
    koppen_class: str
    description: str
    temperature_range_c: tuple[float, float]
    annual_rainfall_mm: float
    humidity_pct: float
    wind_zone: str
    seismic_zone: str
    recommended_materials: list[str]
    construction_season: str
    hazards: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "koppen_class": self.koppen_class,
            "description": self.description,
            "temperature_range_c": list(self.temperature_range_c),
            "annual_rainfall_mm": self.annual_rainfall_mm,
            "humidity_pct": self.humidity_pct,
            "wind_zone": self.wind_zone,
            "seismic_zone": self.seismic_zone,
            "recommended_materials": self.recommended_materials,
            "construction_season": self.construction_season,
            "hazards": self.hazards,
        }


# Simplified climate database by region
CLIMATE_DATABASE: dict[str, ClimateZone] = {
    "semi_arid_south_asia": ClimateZone(
        zone_name="Semi-Arid South Asia",
        koppen_class="BSh",
        description="Hot semi-arid climate with monsoon influence",
        temperature_range_c=(15.0, 45.0),
        annual_rainfall_mm=500.0,
        humidity_pct=45.0,
        wind_zone="interior_south_asia",
        seismic_zone="punjab",
        recommended_materials=["treated_bamboo", "stabilized_mud_brick", "corrugated_tin"],
        construction_season="October to March (dry season)",
        hazards=["monsoon flooding", "dust storms", "extreme heat"],
    ),
    "tropical_monsoon": ClimateZone(
        zone_name="Tropical Monsoon",
        koppen_class="Am",
        description="Tropical monsoon with heavy rainfall",
        temperature_range_c=(22.0, 38.0),
        annual_rainfall_mm=2000.0,
        humidity_pct=75.0,
        wind_zone="coastal_south_asia",
        seismic_zone="kashmir",
        recommended_materials=["treated_bamboo", "corrugated_tin", "reclaimed_timber"],
        construction_season="November to February (dry season)",
        hazards=["cyclones", "flooding", "high humidity rot"],
    ),
    "arid_desert": ClimateZone(
        zone_name="Arid Desert",
        koppen_class="BWh",
        description="Hot desert climate with extreme temperature swings",
        temperature_range_c=(5.0, 50.0),
        annual_rainfall_mm=100.0,
        humidity_pct=25.0,
        wind_zone="interior_south_asia",
        seismic_zone="balochistan",
        recommended_materials=["stabilized_mud_brick", "corrugated_tin", "treated_bamboo"],
        construction_season="October to March (cooler months)",
        hazards=["sandstorms", "extreme heat", "flash floods", "seismic"],
    ),
    "temperate_highland": ClimateZone(
        zone_name="Temperate Highland",
        koppen_class="Cwb",
        description="Mild highland climate with cool winters",
        temperature_range_c=(0.0, 28.0),
        annual_rainfall_mm=1200.0,
        humidity_pct=55.0,
        wind_zone="central_asia",
        seismic_zone="khyber_pakhtunkhwa",
        recommended_materials=["reclaimed_timber", "treated_bamboo", "stabilized_mud_brick"],
        construction_season="April to October (warm season)",
        hazards=["snow loads", "seismic", "frost heave"],
    ),
    "east_africa_savanna": ClimateZone(
        zone_name="East Africa Savanna",
        koppen_class="Aw",
        description="Tropical savanna with distinct wet/dry seasons",
        temperature_range_c=(18.0, 35.0),
        annual_rainfall_mm=800.0,
        humidity_pct=50.0,
        wind_zone="east_africa",
        seismic_zone="east_africa_rift",
        recommended_materials=["treated_bamboo", "reclaimed_timber", "corrugated_tin"],
        construction_season="June to September (dry season)",
        hazards=["flooding", "locusts", "seismic (rift valley)"],
    ),
    "caribbean_tropical": ClimateZone(
        zone_name="Caribbean Tropical",
        koppen_class="Af",
        description="Tropical rainforest with hurricane risk",
        temperature_range_c=(24.0, 34.0),
        annual_rainfall_mm=2500.0,
        humidity_pct=80.0,
        wind_zone="caribbean",
        seismic_zone="caribbean",
        recommended_materials=["treated_bamboo", "reclaimed_timber", "steel_connector"],
        construction_season="December to April (dry season)",
        hazards=["hurricanes", "flooding", "high winds", "seismic"],
    ),
}


def lookup_climate(
    latitude: float | None = None,
    longitude: float | None = None,
    region_name: str | None = None,
) -> ClimateZone:
    """
    Look up climate information for a location.

    Args:
        latitude: Geographic latitude (-90 to 90).
        longitude: Geographic longitude (-180 to 180).
        region_name: Named region (e.g., "semi_arid_south_asia").

    Returns:
        ClimateZone with full climate and hazard information.
    """
    # If region name provided, use direct lookup
    if region_name and region_name in CLIMATE_DATABASE:
        return CLIMATE_DATABASE[region_name]

    # Simple coordinate-based classification (simplified)
    if latitude is not None and longitude is not None:
        if 5 <= latitude <= 35 and 60 <= longitude <= 80:
            if latitude < 20:
                return CLIMATE_DATABASE["tropical_monsoon"]
            elif latitude < 28:
                return CLIMATE_DATABASE["semi_arid_south_asia"]
            else:
                return CLIMATE_DATABASE["temperate_highland"]
        elif -5 <= latitude <= 15 and 25 <= longitude <= 52:
            return CLIMATE_DATABASE["east_africa_savanna"]
        elif 15 <= latitude <= 25 and -80 <= longitude <= -60:
            return CLIMATE_DATABASE["caribbean_tropical"]
        elif 20 <= latitude <= 35 and 55 <= longitude <= 75:
            return CLIMATE_DATABASE["arid_desert"]

    # Default
    return CLIMATE_DATABASE["semi_arid_south_asia"]


def list_climate_zones() -> list[dict[str, Any]]:
    """List all available climate zones."""
    return [cz.to_dict() for cz in CLIMATE_DATABASE.values()]


def get_material_recommendations(climate_zone: str) -> list[str]:
    """Get recommended materials for a climate zone."""
    zone = CLIMATE_DATABASE.get(climate_zone)
    if zone is None:
        return ["treated_bamboo", "reclaimed_timber"]  # Safe defaults
    return zone.recommended_materials
