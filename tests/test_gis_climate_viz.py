"""Tests for GIS mapping, climate data, offline PWA, and data visualization."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── GIS Mapping Tests ─────────────────────────────────────────────────

class TestGISMapping:
    def test_map_config(self):
        r = client.get("/api/v1/gis/map-config?lat=33.69&lng=73.05")
        assert r.status_code == 200
        data = r.json()
        assert "center" in data
        assert "tile_layer" in data
        assert "satellite_layer" in data
        assert "terrain_layer" in data

    def test_nearby_hazards(self):
        r = client.get("/api/v1/gis/hazards?lat=33.69&lng=73.05&radius_km=200")
        assert r.status_code == 200
        data = r.json()
        assert data["total_hazards"] >= 0
        assert isinstance(data["hazards"], list)

    def test_terrain_analysis(self):
        r = client.get("/api/v1/gis/terrain?lat=33.69&lng=73.05")
        assert r.status_code == 200
        data = r.json()
        assert "elevation_m" in data
        assert "slope_degrees" in data
        assert "suitability_score" in data
        assert 0 <= data["suitability_score"] <= 100

    def test_distance_calculation(self):
        r = client.get("/api/v1/gis/distance?lat1=33.69&lng1=73.05&lat2=24.86&lng2=67.01")
        assert r.status_code == 200
        data = r.json()
        assert data["distance_km"] > 0
        assert "bearing_degrees" in data
        assert "bearing_compass" in data

    def test_site_markers(self):
        r = client.post("/api/v1/gis/site-markers", json=[
            {"name": "Camp Alpha", "latitude": 33.69, "longitude": 73.05},
            {"name": "Camp Beta", "latitude": 24.86, "longitude": 67.01},
        ])
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert "bounds" in data

    def test_terrain_high_elevation(self):
        r = client.get("/api/v1/gis/terrain?lat=36.0&lng=74.5")
        assert r.status_code == 200
        data = r.json()
        assert data["elevation_m"] > 1000  # Mountain area


# ── Climate Data Tests ────────────────────────────────────────────────

class TestClimateData:
    def test_weather_forecast(self):
        r = client.get("/api/v1/climate/forecast?lat=33.69&lng=73.05&days=3")
        assert r.status_code == 200
        data = r.json()
        assert data["source"] == "Open-Meteo"
        assert len(data["forecasts"]) > 0

    def test_climate_profile(self):
        r = client.get("/api/v1/climate/profile?lat=33.69&lng=73.05")
        assert r.status_code == 200
        data = r.json()
        assert "climate_zone" in data
        assert "frost_risk" in data
        assert "heat_risk" in data
        assert "monsoon_risk" in data
        assert len(data["recommendations"]) > 0

    def test_climate_zones_list(self):
        r = client.get("/api/v1/climate/zones")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0

    def test_desert_climate(self):
        r = client.get("/api/v1/climate/profile?lat=25.0&lng=67.0")
        assert r.status_code == 200
        data = r.json()
        assert "heat_risk" in data


# ── Offline PWA Tests ─────────────────────────────────────────────────

class TestOfflinePWA:
    def test_pwa_config(self):
        r = client.get("/api/v1/offline/config")
        assert r.status_code == 200
        data = r.json()
        assert "service_worker" in data
        assert "cache" in data
        assert "manifest" in data
        assert data["manifest"]["name"] == "PANAGAH — Shelter Design"

    def test_service_worker(self):
        r = client.get("/api/v1/offline/sw.js")
        assert r.status_code == 200
        assert "CACHE_NAME" in r.text
        assert "addEventListener" in r.text

    def test_sync_push(self):
        r = client.post("/api/v1/offline/sync", json={
            "device_id": "device_001",
            "items": [
                {
                    "id": "sync_001",
                    "entity_type": "material",
                    "entity_id": "mat_001",
                    "action": "create",
                    "data": {"name": "Test Material"},
                    "client_timestamp": "2026-08-28T12:00:00",
                },
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["items_received"] == 1

    def test_sync_status(self):
        r = client.get("/api/v1/offline/sync/status")
        assert r.status_code == 200
        assert "pending" in r.json()

    def test_sync_process(self):
        r = client.post("/api/v1/offline/sync/process?device_id=device_001")
        assert r.status_code == 200

    def test_sync_retry(self):
        r = client.post("/api/v1/offline/sync/retry")
        assert r.status_code == 200

    def test_sync_clear(self):
        r = client.post("/api/v1/offline/sync/clear")
        assert r.status_code == 200

    def test_offline_data(self):
        r = client.get("/api/v1/offline/offline-data/prj_001")
        assert r.status_code == 200
        assert "data" in r.json()


# ── Data Visualization Tests ─────────────────────────────────────────

class TestVisualization:
    def test_validation_chart(self):
        r = client.get("/api/v1/charts/validation-results?passed=10&failed=2&warning=3")
        assert r.status_code == 200
        data = r.json()
        assert data["chart_type"] == "doughnut"

    def test_cost_chart(self):
        r = client.get("/api/v1/charts/cost-breakdown?categories=materials:5000,labor:3000")
        assert r.status_code == 200
        data = r.json()
        assert data["chart_type"] == "bar"

    def test_material_chart(self):
        r = client.get("/api/v1/charts/material-distribution?materials=bamboo:40,earth:30")
        assert r.status_code == 200
        data = r.json()
        assert data["chart_type"] == "pie"

    def test_design_comparison(self):
        r = client.post("/api/v1/charts/design-comparison", json=[
            {"name": "Design A", "structural_score": 80, "cost_score": 60},
            {"name": "Design B", "structural_score": 70, "cost_score": 85},
        ])
        assert r.status_code == 200
        data = r.json()
        assert data["chart_type"] == "radar"

    def test_timeline_chart(self):
        r = client.get("/api/v1/charts/timeline?days=7")
        assert r.status_code == 200
        data = r.json()
        assert data["chart_type"] == "line"

    def test_wind_chart(self):
        r = client.get("/api/v1/charts/wind-load")
        assert r.status_code == 200
        assert r.json()["chart_type"] == "bar"

    def test_safety_chart(self):
        r = client.get("/api/v1/charts/safety-factors")
        assert r.status_code == 200
        assert r.json()["chart_type"] == "bar"

    def test_recharts_format(self):
        r = client.get("/api/v1/charts/recharts/bar?data=a:10,b:20,c:30")
        assert r.status_code == 200
        data = r.json()
        assert len(data["data"]) == 3
        assert data["recharts_component"] == "BarChart"
