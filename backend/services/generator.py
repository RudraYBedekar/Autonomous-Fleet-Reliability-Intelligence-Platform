"""
Ground-vehicle telemetry generator.

Simulates exactly 15 street-snapped cars with realistic speed profiles
(0–50 km/h) and intersection idle behaviour. No airborne entities.
"""

from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.schemas.telemetry import VehicleTelemetry, VehicleStatus
from backend.services.routes import (
    URBAN_ROUTES,
    ROUTE_DIFFICULTIES,
    ROUTE_NAMES,
    haversine_m,
    interpolate,
    is_major_stop,
    upcoming_turn_angle,
    curve_speed_cap,
    segment_lengths,
    zone_at_segment,
    zone_speed_limit,
    count_route_turns,
)
from backend.services.fleet_manifest import get_vehicle_manifest

FLEET_SIZE = 15
TICK_INTERVAL_S = 0.1  # 10 Hz
MAX_SPEED_KMH = 50.0
MIN_CRUISE_KMH = 18.0
MAX_CRUISE_KMH = 45.0
ACCEL_KMH_S = 6.0
DECEL_KMH_S = 10.0
BRAKE_DECAY = 2.8  # exponential braking factor
INTERSECTION_IDLE_S = (0.8, 2.0)  # only at major stops
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

    def status(self) -> VehicleStatus:
        if self.idle_ticks_remaining > 0 or self.speed_kmh == 0:
            return "idle"
        if self.in_curve and self.speed_kmh < self.cruise_target_kmh:
            return "decelerating"
        if self.approaching_intersection:
            return "decelerating"
        if self.speed_kmh < self.cruise_target_kmh - 2:
            return "accelerating"
        return "moving"


class FleetGenerator:
    """Manages N=15 ground vehicles on mock urban street routes."""

    def __init__(self, fleet_size: int = FLEET_SIZE) -> None:
        if fleet_size != FLEET_SIZE:
            raise ValueError(f"Fleet size must be exactly {FLEET_SIZE}")
        self._vehicles: list[_VehicleState] = []
        self._init_fleet()

    def _init_fleet(self) -> None:
        for i in range(FLEET_SIZE):
            route_idx = i  # each car gets a unique route
            route = URBAN_ROUTES[route_idx]
            segs = segment_lengths(route)
            manifest = get_vehicle_manifest(_vehicle_id(i + 1))
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
                )
            )

    def _trip_progress_pct(self, v: _VehicleState) -> float:
        traveled = sum(v.segment_lengths[: v.seg_idx])
        if v.seg_idx < len(v.segment_lengths):
            traveled += v.seg_progress * v.segment_lengths[v.seg_idx]
        return min(100.0, (traveled / v.route_total_m) * 100.0)

    def _update_health(self, v: _VehicleState) -> None:
        if v.speed_kmh > 0:
            v.battery_pct = max(5.0, v.battery_pct - 0.008)
        if v.approaching_intersection and v.speed_kmh > 30:
            v.health_score = max(70.0, v.health_score - 0.02)
        elif v.status() == "idle":
            v.battery_pct = min(100.0, v.battery_pct + 0.004)
            v.health_score = min(100.0, v.health_score + 0.01)

    def _upcoming_turn_within_m(self, v: _VehicleState) -> tuple[float, float]:
        """Return (distance_m, turn_angle_deg) for the next bend ahead."""
        route = URBAN_ROUTES[v.route_idx]
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
        route = URBAN_ROUTES[v.route_idx]

        if v.idle_ticks_remaining > 0:
            v.idle_ticks_remaining -= 1
            v.speed_kmh = 0.0
            v.approaching_intersection = False
            v.in_curve = False
            return

        dist_to_turn, turn_angle = self._upcoming_turn_within_m(v)
        at_major_stop = (
            v.seg_progress >= 0.995
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

        zone = zone_at_segment(v.route_idx, v.seg_idx)
        zone_cap = zone_speed_limit(zone)

        target = min(v.cruise_target_kmh, zone_cap)
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
        route = URBAN_ROUTES[v.route_idx]
        if v.speed_kmh <= 0:
            return interpolate(route, v.seg_idx, v.seg_progress)

        distance_m = (v.speed_kmh / 3.6) * TICK_INTERVAL_S
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
                    v.seg_idx = 0
                    v.segment_lengths = segment_lengths(route)
            else:
                v.seg_progress += remaining / seg_len
                remaining = 0

        return interpolate(route, v.seg_idx, v.seg_progress)

    def tick(self) -> list[VehicleTelemetry]:
        """Advance simulation one tick; return validated telemetry for all vehicles."""
        now = datetime.now(timezone.utc)
        payloads: list[VehicleTelemetry] = []

        for v in self._vehicles:
            self._apply_physics(v)
            lat, lng = self._advance_position(v)
            self._update_health(v)
            point = VehicleTelemetry(
                vehicle_id=v.vehicle_id,
                timestamp=now,
                lat=round(lat, 6),
                lng=round(lng, 6),
                speed_kmh=round(v.speed_kmh, 1),
                status=v.status(),
                health_score=round(v.health_score, 1),
                battery_pct=round(v.battery_pct, 1),
                trip_progress_pct=round(self._trip_progress_pct(v), 1),
                passenger_count=v.passenger_count,
                route_difficulty=ROUTE_DIFFICULTIES[v.route_idx],
                route_name=ROUTE_NAMES[v.route_idx],
                road_zone=zone_at_segment(v.route_idx, v.seg_idx),
                turn_count=count_route_turns(URBAN_ROUTES[v.route_idx]),
            )
            payloads.append(point)

        return payloads

    async def run(self, publish) -> None:
        """Continuously generate telemetry and call async publish callback."""
        print(f"FleetGenerator started — {FLEET_SIZE} ground vehicles @ {1 / TICK_INTERVAL_S:.0f} Hz")
        while True:
            try:
                for point in self.tick():
                    await publish(point)
            except Exception as e:
                print(f"FleetGenerator tick error (recovering): {e}")
            await asyncio.sleep(TICK_INTERVAL_S)


# Module-level singleton for producer CLI reuse
_generator: FleetGenerator | None = None


def get_generator() -> FleetGenerator:
    global _generator
    if _generator is None:
        _generator = FleetGenerator()
    return _generator
