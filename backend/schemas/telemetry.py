"""Pydantic schemas for standardized ground-vehicle telemetry."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Redwood City, CA bounding box (OSM-snapped fleet routes)
URBAN_LAT_MIN = 37.473
URBAN_LAT_MAX = 37.502
URBAN_LNG_MIN = -122.255
URBAN_LNG_MAX = -122.214

VehicleStatus = Literal["idle", "moving", "decelerating", "accelerating"]
RouteDifficulty = Literal["basic", "moderate", "complex"]
RoadZone = Literal["highway", "arterial", "residential", "school_zone", "intersection"]


class VehicleTelemetry(BaseModel):
    vehicle_id: str = Field(..., pattern=r"^car-\d{3}$")
    timestamp: datetime
    lat: float = Field(..., ge=URBAN_LAT_MIN, le=URBAN_LAT_MAX)
    lng: float = Field(..., ge=URBAN_LNG_MIN, le=URBAN_LNG_MAX)
    speed_kmh: float = Field(..., ge=0.0, le=50.0)
    status: VehicleStatus
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    battery_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    trip_progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    passenger_count: int = Field(default=0, ge=0, le=6)
    route_difficulty: RouteDifficulty = "basic"
    route_name: str = ""
    road_zone: RoadZone = "residential"
    turn_count: int = Field(default=0, ge=0, le=200)

    @field_validator("vehicle_id")
    @classmethod
    def validate_fleet_pool(cls, value: str) -> str:
        num = int(value.split("-")[1])
        if num < 1 or num > 15:
            raise ValueError("vehicle_id must be car-001 through car-015")
        return value

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_raw(cls, raw: dict | str) -> "VehicleTelemetry":
        import json

        data = json.loads(raw) if isinstance(raw, str) else raw
        # Accept legacy latitude/longitude keys during transition
        if "lat" not in data and "latitude" in data:
            data["lat"] = data["latitude"]
        if "lng" not in data and "longitude" in data:
            data["lng"] = data["longitude"]
        return cls.model_validate(data)
