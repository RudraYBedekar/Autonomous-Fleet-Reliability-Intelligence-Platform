"""
Street routing — OSM centerlines, zone metadata, turn-aware physics.
"""

from __future__ import annotations

import math
from typing import Literal, Sequence

from backend.services.street_routes_data import (
    URBAN_ROUTES as _RAW_ROUTES,
    ROUTE_ZONES as _RAW_ZONES,
    ROUTE_DIFFICULTIES,
    ROUTE_NAMES,
    ROUTE_FEATURES,
    MAP_CENTER,
    RouteZone,
)

STOP_TURN_THRESHOLD_DEG = 55.0

ZONE_SPEED_LIMITS: dict[RouteZone, float] = {
    "highway": 50.0,
    "arterial": 45.0,
    "residential": 35.0,
    "school_zone": 25.0,
    "intersection": 18.0,
}

ZONE_COLORS: dict[RouteZone, tuple[int, int, int, int]] = {
    "highway": (59, 130, 246, 210),
    "arterial": (34, 197, 94, 210),
    "residential": (148, 163, 184, 200),
    "school_zone": (250, 204, 21, 230),
    "intersection": (239, 68, 68, 230),
}


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    d_lng = math.radians(lng2 - lng1)
    y = math.sin(d_lng) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(d_lng)
    return math.degrees(math.atan2(y, x))


def _angle_diff(a: float, b: float) -> float:
    return abs((b - a + 180) % 360 - 180)


def turn_angle(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> float:
    b1 = _bearing(p0[0], p0[1], p1[0], p1[1])
    b2 = _bearing(p1[0], p1[1], p2[0], p2[1])
    return _angle_diff(b1, b2)


def _dedupe(points: list[tuple[float, float]], min_m: float = 0.5) -> list[tuple[float, float]]:
    if not points:
        return points
    out = [points[0]]
    for pt in points[1:]:
        if haversine_m(out[-1][0], out[-1][1], pt[0], pt[1]) >= min_m:
            out.append(pt)
    return out


def densify_route(
    waypoints: Sequence[tuple[float, float]],
    step_m: float = 8.0,
) -> list[tuple[float, float]]:
    if len(waypoints) < 2:
        return list(waypoints)

    out: list[tuple[float, float]] = [waypoints[0]]
    for i in range(len(waypoints) - 1):
        lat1, lng1 = waypoints[i]
        lat2, lng2 = waypoints[i + 1]
        seg_len = haversine_m(lat1, lng1, lat2, lng2)
        if seg_len <= step_m:
            out.append((lat2, lng2))
            continue
        steps = max(1, int(seg_len / step_m))
        for s in range(1, steps + 1):
            t = s / steps
            out.append((lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t))
    return _dedupe(out, 1.0)


def _expand_zones(raw_route: Sequence[tuple[float, float]], raw_zones: Sequence[RouteZone], dense: Sequence[tuple[float, float]]) -> list[RouteZone]:
    if len(dense) < 2:
        return list(raw_zones)
    if len(raw_zones) != len(raw_route) - 1:
        return [raw_zones[0] if raw_zones else "residential"] * (len(dense) - 1)

    raw_cumulative = [0.0]
    for i in range(len(raw_route) - 1):
        raw_cumulative.append(raw_cumulative[-1] + haversine_m(raw_route[i][0], raw_route[i][1], raw_route[i + 1][0], raw_route[i + 1][1]))

    dense_cumulative = [0.0]
    for i in range(len(dense) - 1):
        dense_cumulative.append(dense_cumulative[-1] + haversine_m(dense[i][0], dense[i][1], dense[i + 1][0], dense[i + 1][1]))

    total_raw = raw_cumulative[-1] or 1.0
    total_dense = dense_cumulative[-1] or 1.0
    expanded: list[RouteZone] = []
    for i in range(len(dense) - 1):
        frac = dense_cumulative[i + 1] / total_dense
        raw_dist = frac * total_raw
        seg_idx = 0
        while seg_idx < len(raw_cumulative) - 2 and raw_cumulative[seg_idx + 1] < raw_dist:
            seg_idx += 1
        expanded.append(raw_zones[min(seg_idx, len(raw_zones) - 1)])
    return expanded


def _build_processed_routes() -> tuple[list[list[tuple[float, float]]], list[list[RouteZone]]]:
    routes: list[list[tuple[float, float]]] = []
    zones: list[list[RouteZone]] = []
    for raw, raw_z in zip(_RAW_ROUTES, _RAW_ZONES):
        dense = densify_route(raw, step_m=10.0)
        routes.append(dense)
        zones.append(_expand_zones(raw, raw_z, dense))
    return routes, zones


URBAN_ROUTES, ROUTE_ZONES = _build_processed_routes()


def segment_lengths(route: Sequence[tuple[float, float]]) -> list[float]:
    return [haversine_m(route[i][0], route[i][1], route[i + 1][0], route[i + 1][1]) for i in range(len(route) - 1)]


def zone_at_segment(route_index: int, seg_idx: int) -> RouteZone:
    zones = ROUTE_ZONES[route_index]
    if not zones:
        return "residential"
    return zones[min(seg_idx, len(zones) - 1)]


def zone_speed_limit(zone: RouteZone) -> float:
    return ZONE_SPEED_LIMITS.get(zone, 35.0)


def count_route_turns(route: Sequence[tuple[float, float]], threshold: float = 15.0) -> int:
    return sum(
        1 for i in range(1, len(route) - 1)
        if turn_angle(route[i - 1], route[i], route[i + 1]) >= threshold
    )


def upcoming_turn_angle(route: Sequence[tuple[float, float]], seg_idx: int) -> float:
    if seg_idx + 2 >= len(route):
        return 0.0
    return turn_angle(route[seg_idx], route[seg_idx + 1], route[seg_idx + 2])


def is_major_stop(_route_index: int, waypoint_index: int, route_len: int, route: Sequence[tuple[float, float]]) -> bool:
    if waypoint_index <= 0 or waypoint_index >= route_len - 1:
        return True
    p0, p1, p2 = route[waypoint_index - 1], route[waypoint_index], route[waypoint_index + 1]
    return turn_angle(p0, p1, p2) >= STOP_TURN_THRESHOLD_DEG


def curve_speed_cap(cruise_kmh: float, turn_angle_deg: float) -> float:
    if turn_angle_deg < 12:
        return cruise_kmh
    factor = 1.0 - (min(turn_angle_deg, 85.0) / 85.0) * 0.38
    return max(20.0, cruise_kmh * factor)


def interpolate(route: Sequence[tuple[float, float]], seg_idx: int, progress: float) -> tuple[float, float]:
    progress = max(0.0, min(1.0, progress))
    lat1, lng1 = route[seg_idx]
    lat2, lng2 = route[seg_idx + 1]
    return lat1 + (lat2 - lat1) * progress, lng1 + (lng2 - lng1) * progress


def build_direct_route(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
    step_m: float = 12.0,
) -> list[tuple[float, float]]:
    """Street-style direct path between two points (densified for simulation)."""
    return densify_route([(from_lat, from_lng), (to_lat, to_lng)], step_m=step_m)


def route_path_lng_lat(route: Sequence[tuple[float, float]]) -> list[list[float]]:
    return [[pt[1], pt[0]] for pt in route]


def route_path_by_zone(route_index: int) -> list[dict]:
    """Colored path segments for map rendering."""
    route = URBAN_ROUTES[route_index]
    zones = ROUTE_ZONES[route_index]
    paths: list[dict] = []
    if len(route) < 2:
        return paths
    current_zone = zones[0]
    current_path = [[route[0][1], route[0][0]]]
    for i in range(len(route) - 1):
        current_path.append([route[i + 1][1], route[i + 1][0]])
        seg_zone = zones[i] if i < len(zones) else current_zone
        next_zone = zones[i + 1] if i + 1 < len(zones) else seg_zone
        if next_zone != current_zone and len(current_path) >= 2:
            paths.append({"path": current_path, "zone": current_zone, "color": ZONE_COLORS[current_zone]})
            current_zone = next_zone
            current_path = [[route[i + 1][1], route[i + 1][0]]]
        else:
            current_zone = seg_zone
    if len(current_path) >= 2:
        paths.append({"path": current_path, "zone": current_zone, "color": ZONE_COLORS[current_zone]})
    return paths


is_intersection = is_major_stop
