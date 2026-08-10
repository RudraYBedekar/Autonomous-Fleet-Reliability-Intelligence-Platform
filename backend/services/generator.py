"""
Ground-vehicle telemetry generator.

Simulates exactly 15 electric street-snapped cars with realistic speed profiles
(0–50 km/h), intersection idle behaviour, and automatic low-battery rerouting
to the nearest EV charging station.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.schemas.telemetry import VehicleTelemetry, VehicleStatus
from backend.services.routes import (
    URBAN_ROUTES,
    ROUTE_DIFFICULTIES,
    ROUTE_NAMES,
    build_direct_route,
    haversine_m,
    interpolate,
    is_major_stop,
    upcoming_turn_angle,
    curve_speed_cap,
    segment_lengths,
    zone_at_segment,
    zone_speed_limit,
    count_route_turns,
    route_path_lng_lat,
)
from backend.services.fleet_manifest import get_vehicle_manifest
from backend.services.trip_insights import compute_eta_minutes, compute_trip_status, compute_maintenance_rul
from backend.services.alerts import evaluate_alerts, push_alerts
from backend.services.charging_stations import (
    BATTERY_CRITICAL_PCT,
    BATTERY_RESTORE_PCT,
    CHARGE_RATE_AT_STATION,
    CHARGE_RATE_IDLE,
    nearest_station,
)

FLEET_SIZE = 15
TICK_INTERVAL_S = 0.1  # 10 Hz
MAX_SPEED_KMH = 50.0
MIN_CRUISE_KMH = 18.0
MAX_CRUISE_KMH = 45.0
ACCEL_KMH_S = 6.0
DECEL_KMH_S = 10.0
INTERSECTION_IDLE_S = (0.8, 2.0)
CURVE_LOOKAHEAD_M = 40.0


def _vehicle_id(index: int) -> str:
    return f"car-{index:03d}"


@dataclass
class _VehicleState:
    vehicle_id: str
    route_idx: int
    seg_idx: int
    seg_progress: float
    speed_kmh: float
    cruise_target_kmh: float
    idle_ticks_remaining: int = 0
    approaching_intersection: bool = False
    in_curve: bool = False
    segment_lengths: list[float] = field(default_factory=list)
    route_total_m: float = 0.0
    health_score: float = 95.0
    battery_pct: float = 90.0
    passenger_count: int = 0
    idle_seconds: float = 0.0
    distance_traveled_m: float = 0.0
    baseline_maintenance_rul: float = 85.0
    vehicle_type: str = "electric"
    original_route_idx: int | None = None
    override_route: list[tuple[float, float]] | None = None
    routing_to_charger: bool = False
    at_charger: bool = False
    charger_station_id: str | None = None
    charger_name: str | None = None
    charger_address: str | None = None
    charger_lat: float | None = None
    charger_lng: float | None = None

    def status(self) -> VehicleStatus:
        if self.at_charger or self.idle_ticks_remaining > 0 or self.speed_kmh == 0:
            return "idle"
        if self.in_curve and self.speed_kmh < self.cruise_target_kmh:
            return "decelerating"
        if self.approaching_intersection:
            return "decelerating"
        if self.speed_kmh < self.cruise_target_kmh - 2:
            return "accelerating"
        return "moving"


class FleetGenerator:
    """Manages N=15 electric ground vehicles on mock urban street routes."""

    def __init__(self, fleet_size: int = FLEET_SIZE) -> None:
        if fleet_size != FLEET_SIZE:
            raise ValueError(f"Fleet size must be exactly {FLEET_SIZE}")
        self._vehicles: list[_VehicleState] = []
        self._latest_telemetry_snapshot: dict[str, VehicleTelemetry] = {}
        self._init_fleet()

    def _init_fleet(self) -> None:
        for i in range(FLEET_SIZE):
            route_idx = i
            route = URBAN_ROUTES[route_idx]
            segs = segment_lengths(route)
            manifest = get_vehicle_manifest(_vehicle_id(i + 1))
            baseline_rul = 100.0
            if manifest:
                baseline_rul = max(15.0, min(100.0, (manifest.maintenance_due_km / 35.0) * 10))
            seg_count = len(route) - 1
            start_seg = random.randint(0, max(0, seg_count - 1))
            self._vehicles.append(
                _VehicleState(
                    vehicle_id=_vehicle_id(i + 1),
                    route_idx=route_idx,
                    seg_idx=start_seg,
                    seg_progress=random.uniform(0.05, 0.85),
                    speed_kmh=random.uniform(8.0, 22.0),
                    cruise_target_kmh=random.uniform(MIN_CRUISE_KMH, MAX_CRUISE_KMH),
                    idle_ticks_remaining=0,
                    segment_lengths=segs,
                    route_total_m=max(sum(segs), 1.0),
                    health_score=manifest.health_score if manifest else random.uniform(85, 99),
                    battery_pct=manifest.battery_pct if manifest else random.uniform(60, 100),
                    passenger_count=manifest.passenger_count if manifest else random.randint(1, 4),
                    baseline_maintenance_rul=baseline_rul,
                )
            )

    def _current_route(self, v: _VehicleState) -> list[tuple[float, float]]:
        if v.override_route and len(v.override_route) >= 2:
            return v.override_route
        return URBAN_ROUTES[v.route_idx]

    def _reset_route_progress(self, v: _VehicleState, route: list[tuple[float, float]]) -> None:
        v.seg_idx = 0
        v.seg_progress = 0.05
        v.segment_lengths = segment_lengths(route)
        v.route_total_m = max(sum(v.segment_lengths), 1.0)
        v.idle_seconds = 0.0

    def _zone_for_vehicle(self, v: _VehicleState) -> str:
        if v.override_route:
            return "arterial"
        return zone_at_segment(v.route_idx, v.seg_idx)

    def _trip_progress_pct(self, v: _VehicleState) -> float:
        traveled = sum(v.segment_lengths[: v.seg_idx])
        if v.seg_idx < len(v.segment_lengths):
            traveled += v.seg_progress * v.segment_lengths[v.seg_idx]
        return min(100.0, (traveled / v.route_total_m) * 100.0)

    def _position(self, v: _VehicleState) -> tuple[float, float]:
        route = self._current_route(v)
        idx = min(v.seg_idx, len(route) - 2)
        return interpolate(route, idx, v.seg_progress)

    def _maybe_reroute_to_charger(self, v: _VehicleState, lat: float, lng: float) -> None:
        if v.at_charger or v.routing_to_charger:
            return
        if v.battery_pct >= BATTERY_CRITICAL_PCT:
            return

        station = nearest_station(lat, lng)
        charge_route = build_direct_route(lat, lng, station.lat, station.lng)
        if len(charge_route) < 2:
            return

        v.original_route_idx = v.original_route_idx if v.original_route_idx is not None else v.route_idx
        v.override_route = charge_route
        v.routing_to_charger = True
        v.charger_station_id = station.station_id
        v.charger_name = station.name
        v.charger_address = station.address
        v.charger_lat = station.lat
        v.charger_lng = station.lng
        v.cruise_target_kmh = min(v.cruise_target_kmh, 35.0)
        self._reset_route_progress(v, charge_route)

    def _restore_passenger_route(self, v: _VehicleState) -> None:
        restore_idx = v.original_route_idx if v.original_route_idx is not None else v.route_idx
        v.route_idx = restore_idx
        v.override_route = None
        v.routing_to_charger = False
        v.at_charger = False
        v.charger_station_id = None
        v.charger_name = None
        v.charger_address = None
        v.charger_lat = None
        v.charger_lng = None
        v.original_route_idx = None
        route = URBAN_ROUTES[v.route_idx]
        self._reset_route_progress(v, route)

    def _handle_charging(self, v: _VehicleState) -> None:
        v.speed_kmh = 0.0
        v.idle_ticks_remaining = 0
        v.approaching_intersection = False
        v.in_curve = False
        v.battery_pct = min(100.0, v.battery_pct + CHARGE_RATE_AT_STATION)
        v.health_score = min(100.0, v.health_score + 0.02)
        if v.battery_pct >= BATTERY_RESTORE_PCT:
            self._restore_passenger_route(v)

    def _update_health(self, v: _VehicleState) -> None:
        if v.at_charger:
            return
        if v.speed_kmh > 0:
            v.battery_pct = max(5.0, v.battery_pct - 0.008)
        if v.approaching_intersection and v.speed_kmh > 30:
            v.health_score = max(70.0, v.health_score - 0.02)
        elif v.status() == "idle":
            v.battery_pct = min(100.0, v.battery_pct + CHARGE_RATE_IDLE)
            v.health_score = min(100.0, v.health_score + 0.01)

    def _upcoming_turn_within_m(self, v: _VehicleState) -> tuple[float, float]:
        route = self._current_route(v)
        dist = (1.0 - v.seg_progress) * v.segment_lengths[v.seg_idx]
        angle = upcoming_turn_angle(route, v.seg_idx)

        if angle >= 12:
            return dist, angle

        idx = v.seg_idx + 1
        while idx < len(v.segment_lengths):
            dist += v.segment_lengths[idx]
            angle = upcoming_turn_angle(route, idx)
            if angle >= 12:
                return dist, angle
            idx += 1
        return 999.0, 0.0

    def _apply_physics(self, v: _VehicleState) -> None:
        route = self._current_route(v)

        if v.idle_ticks_remaining > 0:
            v.idle_ticks_remaining -= 1
            v.speed_kmh = 0.0
            v.idle_seconds += TICK_INTERVAL_S
            v.approaching_intersection = False
            v.in_curve = False
            return

        if v.speed_kmh < 1.0:
            v.idle_seconds += TICK_INTERVAL_S
        else:
            v.idle_seconds = 0.0

        dist_to_turn, turn_angle = self._upcoming_turn_within_m(v)
        at_major_stop = (
            not v.override_route
            and v.seg_progress >= 0.995
            and v.seg_idx + 1 < len(route)
            and is_major_stop(v.route_idx, v.seg_idx + 1, len(route), route)
        )

        if at_major_stop:
            v.speed_kmh = 0.0
            idle_s = random.uniform(*INTERSECTION_IDLE_S)
            v.idle_ticks_remaining = max(1, int(idle_s / TICK_INTERVAL_S))
            v.approaching_intersection = False
            v.in_curve = False
            return

        v.in_curve = turn_angle >= 12 and dist_to_turn <= CURVE_LOOKAHEAD_M
        v.approaching_intersection = turn_angle >= 45 and dist_to_turn <= 20.0

        zone = self._zone_for_vehicle(v)
        zone_cap = zone_speed_limit(zone)

        target = min(v.cruise_target_kmh, zone_cap)
        if v.routing_to_charger:
            target = min(target, 35.0)
        if v.in_curve:
            proximity = max(0.0, 1.0 - dist_to_turn / CURVE_LOOKAHEAD_M)
            curve_cap = min(zone_cap, curve_speed_cap(v.cruise_target_kmh, turn_angle))
            target = v.cruise_target_kmh - proximity * (v.cruise_target_kmh - curve_cap)
            target = min(target, zone_cap)

        if v.speed_kmh < target:
            v.speed_kmh = min(target, v.speed_kmh + ACCEL_KMH_S * TICK_INTERVAL_S)
        elif v.speed_kmh > target + 1.5:
            v.speed_kmh = max(target, v.speed_kmh - DECEL_KMH_S * TICK_INTERVAL_S * 0.6)

        v.speed_kmh = max(0.0, min(MAX_SPEED_KMH, v.speed_kmh))

    def _advance_position(self, v: _VehicleState) -> tuple[float, float]:
        route = self._current_route(v)
        if v.speed_kmh <= 0:
            return self._position(v)

        distance_m = (v.speed_kmh / 3.6) * TICK_INTERVAL_S
        v.distance_traveled_m += distance_m
        remaining = distance_m

        while remaining > 0 and v.seg_idx < len(route) - 1:
            seg_len = v.segment_lengths[v.seg_idx]
            if seg_len <= 0:
                v.seg_idx += 1
                v.seg_progress = 0.0
                continue

            dist_left_on_seg = (1.0 - v.seg_progress) * seg_len
            if remaining >= dist_left_on_seg:
                remaining -= dist_left_on_seg
                v.seg_idx += 1
                v.seg_progress = 0.0
                if v.seg_idx >= len(route) - 1:
                    if v.routing_to_charger:
                        v.routing_to_charger = False
                        v.at_charger = True
                        v.speed_kmh = 0.0
                        return route[-1]
                    v.seg_idx = 0
                    v.segment_lengths = segment_lengths(route)
            else:
                v.seg_progress += remaining / seg_len
                remaining = 0

        return interpolate(route, min(v.seg_idx, len(route) - 2), v.seg_progress)

    def _resolve_trip_status(self, v: _VehicleState, progress: float) -> str:
        if v.at_charger:
            return "charging"
        if v.routing_to_charger:
            return "routing_to_charger"
        return compute_trip_status(progress, v.speed_kmh, v.idle_seconds)

    def _route_name(self, v: _VehicleState) -> str:
        if v.routing_to_charger and v.charger_name:
            return f"EV charge → {v.charger_name}"
        if v.at_charger and v.charger_name:
            return f"Charging @ {v.charger_name}"
        return ROUTE_NAMES[v.route_idx]

    def tick(self) -> list[VehicleTelemetry]:
        now = datetime.now(timezone.utc)
        payloads: list[VehicleTelemetry] = []

        for v in self._vehicles:
            if v.at_charger:
                self._handle_charging(v)
                lat, lng = self._position(v)
            else:
                lat, lng = self._position(v)
                self._maybe_reroute_to_charger(v, lat, lng)
                self._apply_physics(v)
                lat, lng = self._advance_position(v)
                self._update_health(v)

            progress = self._trip_progress_pct(v)
            eta = compute_eta_minutes(progress, v.route_total_m, v.speed_kmh)
            trip_status = self._resolve_trip_status(v, progress)
            maintenance_rul = compute_maintenance_rul(v.baseline_maintenance_rul, v.distance_traveled_m)
            route = self._current_route(v)

            nav_mode = "emergency_charge" if (v.routing_to_charger or v.at_charger) else "passenger_trip"
            dest_address = v.charger_address if (v.routing_to_charger or v.at_charger) else None
            live_path = route_path_lng_lat(route) if v.override_route else None

            point = VehicleTelemetry(
                vehicle_id=v.vehicle_id,
                timestamp=now,
                lat=round(lat, 6),
                lng=round(lng, 6),
                speed_kmh=round(v.speed_kmh, 1),
                status=v.status(),
                health_score=round(v.health_score, 1),
                battery_pct=round(v.battery_pct, 1),
                trip_progress_pct=round(progress, 1),
                passenger_count=v.passenger_count,
                vehicle_type="electric",
                route_difficulty=ROUTE_DIFFICULTIES[v.route_idx],
                route_name=self._route_name(v),
                road_zone=self._zone_for_vehicle(v),
                turn_count=count_route_turns(route),
                eta_minutes=eta,
                trip_status=trip_status,
                maintenance_rul_pct=round(maintenance_rul, 1),
                navigation_mode=nav_mode,
                destination_address=dest_address,
                route_path_live=live_path,
                charger_station_id=v.charger_station_id,
                charger_station_name=v.charger_name,
            )

            alerts = evaluate_alerts(point, idle_seconds=v.idle_seconds)
            if alerts:
                push_alerts(alerts)
                top = max(alerts, key=lambda a: {"critical": 3, "warning": 2, "info": 1}[a.severity])
                point = point.model_copy(update={
                    "active_alert": top.message,
                    "alert_severity": top.severity,
                })

            self._latest_telemetry_snapshot[point.vehicle_id] = point
            payloads.append(point)

        return payloads

    def get_latest(self, vehicle_id: str | None = None) -> dict[str, VehicleTelemetry] | VehicleTelemetry | None:
        if vehicle_id:
            return self._latest_telemetry_snapshot.get(vehicle_id)
        return self._latest_telemetry_snapshot

    async def run(self, publish) -> None:
        print(f"FleetGenerator started — {FLEET_SIZE} EVs @ {1 / TICK_INTERVAL_S:.0f} Hz")
        while True:
            try:
                for point in self.tick():
                    await publish(point)
            except Exception as e:
                print(f"FleetGenerator tick error (recovering): {e}")
            await asyncio.sleep(TICK_INTERVAL_S)


_generator: FleetGenerator | None = None


def get_generator() -> FleetGenerator:
    global _generator
    if _generator is None:
        _generator = FleetGenerator()
    return _generator
