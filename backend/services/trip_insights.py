"""ETA, trip status, and maintenance RUL helpers."""

from __future__ import annotations

from typing import Literal

TripStatus = Literal["at_pickup", "en_route", "delayed", "at_destination", "idle"]


def compute_eta_minutes(
    trip_progress_pct: float,
    route_total_m: float,
    speed_kmh: float,
) -> float | None:
    if route_total_m <= 0 or speed_kmh < 2.0:
        return None
    remaining_m = route_total_m * max(0.0, 1.0 - trip_progress_pct / 100.0)
    if remaining_m < 5:
        return 0.0
    hours = remaining_m / 1000.0 / max(speed_kmh, 2.0)
    return round(hours * 60.0, 1)


def compute_trip_status(
    trip_progress_pct: float,
    speed_kmh: float,
    idle_seconds: float,
) -> TripStatus:
    if trip_progress_pct >= 97:
        return "at_destination"
    if trip_progress_pct <= 3 and speed_kmh < 3:
        return "at_pickup"
    if idle_seconds >= 30 and 5 < trip_progress_pct < 95:
        return "delayed"
    if speed_kmh < 1 and idle_seconds >= 8:
        return "idle"
    return "en_route"


def compute_maintenance_rul(
    baseline_rul_pct: float,
    distance_traveled_m: float,
) -> float:
    """Degrade RUL slowly with distance traveled."""
    wear = (distance_traveled_m / 1000.0) * 1.2
    return max(0.0, min(100.0, baseline_rul_pct - wear))
