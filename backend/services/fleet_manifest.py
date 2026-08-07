"""Fleet manifest — Redwood City pickup/destination, routes, passengers, health."""

from __future__ import annotations

import random
from dataclasses import dataclass

from backend.services.routes import URBAN_ROUTES, ROUTE_DIFFICULTIES, ROUTE_NAMES, ROUTE_FEATURES, haversine_m, count_route_turns, route_path_by_zone
from backend.services.street_routes_data import CITY_NAME

# Known Redwood City, CA locations (address, lat, lng)
RWC_PLACES: list[tuple[str, float, float]] = [
    ("2650 Broadway, Redwood City, CA 94063", 37.4857, -122.2322),       # Caltrain
    ("2200 Broadway, Redwood City, CA 94063", 37.4862, -122.2445),       # Courthouse Sq
    ("850 Main St, Redwood City, CA 94063", 37.4858, -122.2325),
    ("909 Main St, Redwood City, CA 94063", 37.4865, -122.2318),
    ("1044 Middlefield Rd, Redwood City, CA 94063", 37.4842, -122.2288),
    ("3017 Middlefield Rd, Redwood City, CA 94063", 37.4920, -122.2278),
    ("1450 Veterans Blvd, Redwood City, CA 94063", 37.4918, -122.2370),
    ("600 El Camino Real, Redwood City, CA 94063", 37.4785, -122.2358),
    ("1201 El Camino Real, Redwood City, CA 94063", 37.4900, -122.2348),
    ("2500 El Camino Real, Redwood City, CA 94063", 37.4946, -122.2344),
    ("751 Bradford St, Redwood City, CA 94063", 37.4840, -122.2310),
    ("801 Laurel St, Redwood City, CA 94063", 37.4835, -122.2345),
    ("500 Arguello St, Redwood City, CA 94063", 37.4880, -122.2330),
    ("450 Jefferson Ave, Redwood City, CA 94063", 37.4830, -122.2405),
    ("1100 Bay Rd, Redwood City, CA 94063", 37.4800, -122.2385),
    ("3505 Edison Way, Redwood City, CA 94063", 37.4910, -122.2290),
    ("1500 Maple St, Redwood City, CA 94063", 37.4875, -122.2300),
    ("2107 Broadway, Redwood City, CA 94063", 37.4870, -122.2425),
    ("3300 Brittan Ave, Redwood City, CA 94063", 37.4945, -122.2276),
    ("1800 El Camino Real, Redwood City, CA 94063", 37.4827, -122.2356),
    ("Redwood City Public Library, 1044 Middlefield Rd, Redwood City, CA 94063", 37.4845, -122.2284),
    ("Sequoia Hospital, 170 Alameda de las Pulgas, Redwood City, CA 94062", 37.4848, -122.2470),
    ("Redwood Shores Pkwy & Marine Pkwy, Redwood City, CA 94065", 37.4920, -122.2295),
    ("Stanford in Redwood City, 2665 Broadway, Redwood City, CA 94063", 37.4878, -122.2335),
    ("Kaiser Permanente, 1150 Veterans Blvd, Redwood City, CA 94063", 37.4915, -122.2395),
]

# Per-vehicle trip pairs — all Redwood City (pickup → destination)
TRIP_PAIRS: list[tuple[str, str]] = [
    ("600 El Camino Real, Redwood City, CA 94063", "2500 El Camino Real, Redwood City, CA 94063"),
    ("2650 Broadway, Redwood City, CA 94063", "2200 Broadway, Redwood City, CA 94063"),
    ("2200 Broadway, Redwood City, CA 94063", "850 Main St, Redwood City, CA 94063"),
    ("1450 Veterans Blvd, Redwood City, CA 94063", "3505 Edison Way, Redwood City, CA 94063"),
    ("1044 Middlefield Rd, Redwood City, CA 94063", "3017 Middlefield Rd, Redwood City, CA 94063"),
    ("850 Main St, Redwood City, CA 94063", "909 Main St, Redwood City, CA 94063"),
    ("450 Jefferson Ave, Redwood City, CA 94063", "500 Arguello St, Redwood City, CA 94063"),
    ("751 Bradford St, Redwood City, CA 94063", "1500 Maple St, Redwood City, CA 94063"),
    ("1100 Bay Rd, Redwood City, CA 94063", "1201 El Camino Real, Redwood City, CA 94063"),
    ("1800 El Camino Real, Redwood City, CA 94063", "Stanford in Redwood City, 2665 Broadway, Redwood City, CA 94063"),
    ("909 Main St, Redwood City, CA 94063", "801 Laurel St, Redwood City, CA 94063"),
    ("2107 Broadway, Redwood City, CA 94063", "Kaiser Permanente, 1150 Veterans Blvd, Redwood City, CA 94063"),
    ("Redwood City Public Library, 1044 Middlefield Rd, Redwood City, CA 94063", "3300 Brittan Ave, Redwood City, CA 94063"),
    ("Sequoia Hospital, 170 Alameda de las Pulgas, Redwood City, CA 94062", "Redwood Shores Pkwy & Marine Pkwy, Redwood City, CA 94065"),
    ("2650 Broadway, Redwood City, CA 94063", "3505 Edison Way, Redwood City, CA 94063"),
]


@dataclass
class VehicleManifest:
    vehicle_id: str
    route_idx: int
    route_name: str
    route_difficulty: str
    city: str
    pickup_address: str
    destination_address: str
    pickup_lat: float
    pickup_lng: float
    destination_lat: float
    destination_lng: float
    route_path: list[list[float]]
    passenger_count: int
    health_score: float
    battery_pct: float
    engine_status: str
    odometer_km: float
    maintenance_due_km: float
    driver_name: str
    driver_phone: str
    route_features: list[str]
    turn_count: int

    def to_dict(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "route_idx": self.route_idx,
            "route_name": self.route_name,
            "route_difficulty": self.route_difficulty,
            "city": self.city,
            "pickup_address": self.pickup_address,
            "destination_address": self.destination_address,
            "pickup_lat": self.pickup_lat,
            "pickup_lng": self.pickup_lng,
            "destination_lat": self.destination_lat,
            "destination_lng": self.destination_lng,
            "route_path": self.route_path,
            "passenger_count": self.passenger_count,
            "health_score": round(self.health_score, 1),
            "battery_pct": round(self.battery_pct, 1),
            "engine_status": self.engine_status,
            "odometer_km": round(self.odometer_km, 1),
            "maintenance_due_km": round(self.maintenance_due_km, 1),
            "driver_name": self.driver_name,
            "driver_phone": self.driver_phone,
            "vehicle_type": "electric",
            "powertrain": "BEV",
            "route_features": self.route_features,
            "turn_count": self.turn_count,
            "route_zones_path": route_path_by_zone(self.route_idx),
        }


def _driver_phone(index: int) -> str:
    return f"+1 (650) 555-{index + 101:04d}"


DRIVER_NAMES = [
    "Alex Rivera", "Jordan Kim", "Sam Patel", "Taylor Nguyen", "Casey Brooks",
    "Morgan Lee", "Riley Chen", "Jamie Ortiz", "Quinn Davis", "Avery Singh",
    "Drew Martinez", "Blake Johnson", "Skyler Wong", "Reese Garcia", "Finley Shah",
]

ENGINE_STATUSES = ["normal", "normal", "normal", "normal", "watch"]
PASSENGER_COUNTS = [2, 1, 3, 4, 2, 1, 3, 2, 4, 1, 2, 3, 1, 4, 2]


def _nearest_place(lat: float, lng: float) -> tuple[str, float, float]:
    best = min(RWC_PLACES, key=lambda p: haversine_m(lat, lng, p[1], p[2]))
    return best


def _build_manifest(index: int) -> VehicleManifest:
    vehicle_id = f"car-{index + 1:03d}"
    route_idx = index
    route = URBAN_ROUTES[route_idx]

    pickup_lat, pickup_lng = route[0]
    dest_lat, dest_lng = route[-1]

    pickup_address, _, _ = _nearest_place(pickup_lat, pickup_lng)
    dest_address, _, _ = _nearest_place(dest_lat, dest_lng)

    # Prefer explicit trip pair labels when set for this vehicle
    if index < len(TRIP_PAIRS):
        pickup_address, dest_address = TRIP_PAIRS[index]

    return VehicleManifest(
        vehicle_id=vehicle_id,
        route_idx=route_idx,
        route_name=ROUTE_NAMES[route_idx],
        route_difficulty=ROUTE_DIFFICULTIES[route_idx],
        city=CITY_NAME,
        pickup_address=pickup_address,
        destination_address=dest_address,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        destination_lat=dest_lat,
        destination_lng=dest_lng,
        route_path=[[pt[1], pt[0]] for pt in route],
        passenger_count=PASSENGER_COUNTS[index],
        health_score=random.uniform(82, 99),
        battery_pct=random.uniform(55, 100),
        engine_status=random.choice(ENGINE_STATUSES),
        odometer_km=random.uniform(12000, 85000),
        maintenance_due_km=random.uniform(800, 3500),
        driver_name=DRIVER_NAMES[index],
        driver_phone=_driver_phone(index),
        route_features=ROUTE_FEATURES[route_idx] if route_idx < len(ROUTE_FEATURES) else [],
        turn_count=count_route_turns(route),
    )


_manifests: dict[str, VehicleManifest] | None = None


def get_fleet_manifest() -> list[VehicleManifest]:
    global _manifests
    if _manifests is None:
        random.seed(42)
        _manifests = {f"car-{i + 1:03d}": _build_manifest(i) for i in range(15)}
    return list(_manifests.values())


def get_vehicle_manifest(vehicle_id: str) -> VehicleManifest | None:
    get_fleet_manifest()
    assert _manifests is not None
    return _manifests.get(vehicle_id)
