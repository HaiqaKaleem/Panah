"""GIS Mapping service — site locations, terrain analysis, hazard overlay.

Uses OpenStreetMap tiles (free) + Open-Meteo API (free, no key needed).
"""

import math
from typing import Optional
from dataclasses import dataclass

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/gis", tags=["GIS Mapping"])


# ── Models ────────────────────────────────────────────────────────────

class SiteLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: str = Field(default="Site Location")
    altitude_m: Optional[float] = None
    description: Optional[str] = None


class MapBounds(BaseModel):
    north: float
    south: float
    east: float
    west: float


class HazardZone(BaseModel):
    zone_type: str  # flood, earthquake, landslide, wind, fire
    severity: str   # low, moderate, high, extreme
    radius_km: float
    center_lat: float
    center_lng: float
    description: str


class TerrainAnalysis(BaseModel):
    elevation_m: float
    slope_degrees: float
    aspect: str  # north, south, east, west
    soil_type: str
    drainage: str
    vegetation: str
    suitability_score: int  # 0-100


# ── GIS Service ───────────────────────────────────────────────────────

class GISService:
    """GIS mapping and spatial analysis service."""

    # South Asia hazard zones (simplified)
    HAZARD_ZONES = [
        HazardZone(
            zone_type="earthquake", severity="high",
            radius_km=200, center_lat=34.0, center_lng=73.0,
            description="Active seismic zone — Himalayan collision boundary"
        ),
        HazardZone(
            zone_type="flood", severity="moderate",
            radius_km=50, center_lat=33.6, center_lng=73.0,
            description="Indus River floodplain — monsoon flooding risk"
        ),
        HazardZone(
            zone_type="wind", severity="moderate",
            radius_km=100, center_lat=25.0, center_lng=67.0,
            description="Coastal wind zone — cyclone exposure"
        ),
        HazardZone(
            zone_type="landslide", severity="high",
            radius_km=30, center_lat=35.9, center_lng=74.5,
            description="Northern mountains — steep terrain landslide risk"
        ),
    ]

    def get_map_config(self, lat: float, lng: float, zoom: int = 12) -> dict:
        """Generate Leaflet map configuration for a site."""
        return {
            "center": [lat, lng],
            "zoom": zoom,
            "tile_layer": {
                "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "attribution": "© OpenStreetMap contributors",
                "max_zoom": 19,
            },
            "satellite_layer": {
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "attribution": "© Esri",
                "max_zoom": 18,
            },
            "terrain_layer": {
                "url": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                "attribution": "© OpenTopoMap",
                "max_zoom": 17,
            },
        }

    def get_nearby_hazards(self, lat: float, lng: float, radius_km: float = 100) -> list[dict]:
        """Find hazard zones near a location."""
        nearby = []
        for zone in self.HAZARD_ZONES:
            dist = self._haversine(lat, lng, zone.center_lat, zone.center_lng)
            if dist <= zone.radius_km + radius_km:
                nearby.append({
                    "type": zone.zone_type,
                    "severity": zone.severity,
                    "distance_km": round(dist, 1),
                    "description": zone.description,
                    "within_zone": dist <= zone.radius_km,
                })
        return sorted(nearby, key=lambda x: x["distance_km"])

    def analyze_terrain(self, lat: float, lng: float) -> TerrainAnalysis:
        """Analyze terrain suitability for shelter construction."""
        # Simplified terrain model (in production, use DEM data)
        # Elevation approximation based on latitude (very simplified)
        abs_lat = abs(lat)
        if abs_lat > 35:
            elevation = 1500 + (abs_lat - 35) * 200
            soil_type = "rocky mountain soil"
            drainage = "rapid"
            vegetation = "alpine scrub"
        elif abs_lat > 30:
            elevation = 500 + (abs_lat - 30) * 200
            soil_type = "alluvial soil"
            drainage = "moderate"
            vegetation = "agricultural land"
        elif abs_lat > 25:
            elevation = 50 + (abs_lat - 25) * 90
            soil_type = "sandy loam"
            drainage = "slow"
            vegetation = "grassland"
        else:
            elevation = 10
            soil_type = "clay"
            drainage = "poor"
            vegetation = "tropical forest"

        # Slope approximation (simplified)
        slope = min(45, max(0, (elevation / 100) * 3))

        # Aspect (simplified)
        aspects = ["north", "south", "east", "west"]
        aspect = aspects[int(abs(lng * 100)) % 4]

        # Suitability score
        score = 100
        if slope > 30:
            score -= 30
        elif slope > 15:
            score -= 15
        if drainage == "poor":
            score -= 25
        elif drainage == "rapid":
            score -= 10
        if elevation > 2000:
            score -= 20
        elif elevation < 20:
            score -= 10

        return TerrainAnalysis(
            elevation_m=round(elevation, 1),
            slope_degrees=round(slope, 1),
            aspect=aspect,
            soil_type=soil_type,
            drainage=drainage,
            vegetation=vegetation,
            suitability_score=max(0, min(100, score)),
        )

    def calculate_distance(self, lat1: float, lng1: float,
                           lat2: float, lng2: float) -> dict:
        """Calculate distance between two points."""
        dist_km = self._haversine(lat1, lng1, lat2, lng2)
        bearing = self._bearing(lat1, lng1, lat2, lng2)
        return {
            "distance_km": round(dist_km, 2),
            "distance_miles": round(dist_km * 0.621371, 2),
            "bearing_degrees": round(bearing, 1),
            "bearing_compass": self._compass_direction(bearing),
        }

    def get_site_markers(self, sites: list[dict]) -> list[dict]:
        """Generate Leaflet markers for multiple sites."""
        markers = []
        for site in sites:
            lat = site.get("latitude", 0)
            lng = site.get("longitude", 0)
            hazard_level = self._assess_hazard_level(lat, lng)
            markers.append({
                "position": [lat, lng],
                "popup": f"<b>{site.get('name', 'Unknown')}</b><br>"
                         f"Hazard level: {hazard_level}<br>"
                         f"Lat: {lat:.4f}, Lng: {lng:.4f}",
                "icon": self._marker_icon(hazard_level),
                "tooltip": site.get("name", ""),
            })
        return markers

    def get_map_bounds(self, sites: list[dict]) -> MapBounds:
        """Calculate bounding box for multiple sites."""
        if not sites:
            return MapBounds(north=0, south=0, east=0, west=0)
        lats = [s.get("latitude", 0) for s in sites]
        lngs = [s.get("longitude", 0) for s in sites]
        padding = 0.01
        return MapBounds(
            north=max(lats) + padding,
            south=min(lats) - padding,
            east=max(lngs) + padding,
            west=min(lngs) - padding,
        )

    def _haversine(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance in km."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat/2)**2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlng/2)**2)
        return R * 2 * math.asin(math.sqrt(a))

    def _bearing(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate bearing from point 1 to point 2."""
        dlng = math.radians(lng2 - lng1)
        y = math.sin(dlng) * math.cos(math.radians(lat2))
        x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
             math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlng))
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    def _compass_direction(self, bearing: float) -> str:
        """Convert bearing to compass direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = round(bearing / 22.5) % 16
        return directions[idx]

    def _assess_hazard_level(self, lat: float, lng: float) -> str:
        """Assess overall hazard level for a location."""
        nearby = self.get_nearby_hazards(lat, lng, radius_km=50)
        if any(z["severity"] == "extreme" for z in nearby):
            return "extreme"
        if any(z["severity"] == "high" for z in nearby):
            return "high"
        if any(z["severity"] == "moderate" for z in nearby):
            return "moderate"
        return "low"

    def _marker_icon(self, hazard_level: str) -> dict:
        """Get marker icon config based on hazard level."""
        colors = {
            "low": "green", "moderate": "orange",
            "high": "red", "extreme": "darkred",
        }
        return {
            "color": colors.get(hazard_level, "blue"),
            "icon": "home",
            "prefix": "fa",
        }


gis_service = GISService()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.get("/map-config", summary="Get Leaflet map configuration")
async def map_config(
    lat: float = Query(33.6941, description="Center latitude"),
    lng: float = Query(73.0479, description="Center longitude"),
    zoom: int = Query(12, ge=1, le=19),
):
    """Get complete Leaflet map configuration with tile layers."""
    return gis_service.get_map_config(lat, lng, zoom)


@router.get("/hazards", summary="Find nearby hazard zones")
async def nearby_hazards(
    lat: float = Query(..., description="Site latitude"),
    lng: float = Query(..., description="Site longitude"),
    radius_km: float = Query(100, ge=1, le=500),
):
    """Find hazard zones (flood, earthquake, landslide, wind) near a location."""
    hazards = gis_service.get_nearby_hazards(lat, lng, radius_km)
    return {
        "location": {"lat": lat, "lng": lng},
        "search_radius_km": radius_km,
        "total_hazards": len(hazards),
        "hazards": hazards,
    }


@router.get("/terrain", response_model=TerrainAnalysis, summary="Analyze terrain")
async def terrain_analysis(
    lat: float = Query(..., description="Site latitude"),
    lng: float = Query(..., description="Site longitude"),
):
    """Analyze terrain suitability for shelter construction."""
    return gis_service.analyze_terrain(lat, lng)


@router.get("/distance", summary="Calculate distance between points")
async def distance(
    lat1: float = Query(..., description="From latitude"),
    lng1: float = Query(..., description="From longitude"),
    lat2: float = Query(..., description="To latitude"),
    lng2: float = Query(..., description="To longitude"),
):
    """Calculate distance and bearing between two GPS coordinates."""
    return gis_service.calculate_distance(lat1, lng1, lat2, lng2)


@router.post("/site-markers", summary="Generate map markers for sites")
async def site_markers(sites: list[dict]):
    """Generate Leaflet markers with hazard assessment for multiple sites."""
    markers = gis_service.get_site_markers(sites)
    bounds = gis_service.get_map_bounds(sites)
    return {
        "markers": markers,
        "bounds": bounds.model_dump(),
        "total": len(markers),
    }
