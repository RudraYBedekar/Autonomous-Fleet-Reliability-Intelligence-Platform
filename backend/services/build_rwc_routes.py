"""
Build complex OSM-snapped routes with zone metadata (highway, school, turns).
Writes backend/services/street_routes_data.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Literal

OSM_PATH = Path(__file__).with_name("rwc_osm.json")
TARGET = Path(__file__).with_name("street_routes_data.py")
MIN_SEG_M = 45.0
TURN_COUNT_THRESHOLD = 15.0
INTERSECTION_ANGLE = 18.0

RouteZone = Literal["highway", "arterial", "residential", "school_zone", "intersection"]

# Redwood City schools — school-zone segments within ~90 m of these points
SCHOOLS: list[tuple[str, float, float]] = [
    ("Redwood High School", 37.4842, -122.2361),
    ("Kennedy Middle School", 37.4883, -122.2314),
    ("Garfield Elementary", 37.4871, -122.2282),
    ("Roosevelt School", 37.4856, -122.2338),
    ("Adelante Spanish Immersion", 37.4834, -122.2295),
]

HIGHWAY_STREETS = {
    "El Camino Real", "Woodside Road", "Veterans Boulevard", "Middlefield Road",
    "Jefferson Avenue", "Broadway",
}


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def poly_length(poly: list[tuple[float, float]]) -> float:
    return sum(haversine_m(poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1]) for i in range(len(poly) - 1))


def _bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    d_lng = math.radians(lng2 - lng1)
    y = math.sin(d_lng) * math.cos(lat2_r)
    x = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(d_lng)
    return math.degrees(math.atan2(y, x))


def turn_angle(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> float:
    b1 = _bearing(p0[0], p0[1], p1[0], p1[1])
    b2 = _bearing(p1[0], p1[1], p2[0], p2[1])
    return abs((b2 - b1 + 180) % 360 - 180)


class OsmSegment:
    __slots__ = ("name", "points", "length", "highway", "id")

    def __init__(self, name: str, points: list[tuple[float, float]], highway: str):
        self.name = name
        self.points = points
        self.length = poly_length(points)
        self.highway = highway or "unclassified"
        self.id = id(points)


def load_segments() -> list[OsmSegment]:
    with open(OSM_PATH, encoding="utf-8") as f:
        obj = json.load(f)

    out: list[OsmSegment] = []
    for el in obj.get("elements", []):
        name = el.get("tags", {}).get("name")
        geom = el.get("geometry")
        if not name or not geom:
            continue
        pts = [(p["lat"], p["lon"]) for p in geom]
        if len(pts) < 3 or poly_length(pts) < MIN_SEG_M:
            continue
        out.append(OsmSegment(name, pts, el.get("tags", {}).get("highway", "unclassified")))
    out.sort(key=lambda s: s.length, reverse=True)
    return out


def _near_school(lat: float, lng: float, radius_m: float = 150.0) -> bool:
    return any(haversine_m(lat, lng, s[1], s[2]) <= radius_m for s in SCHOOLS)


def _base_zone(name: str, highway: str, mid: tuple[float, float]) -> RouteZone:
    if _near_school(mid[0], mid[1]):
        return "school_zone"
    if highway in ("primary", "trunk") or name in HIGHWAY_STREETS:
        return "highway"
    if highway in ("secondary", "tertiary"):
        return "arterial"
    return "residential"


def boost_school_zones(route: list[tuple[float, float]], zones: list[RouteZone]) -> list[RouteZone]:
    """Mark segments passing near schools as school zones."""
    out = list(zones)
    for i in range(len(route) - 1):
        for pt in (route[i], route[i + 1]):
            if _near_school(pt[0], pt[1], 200.0):
                out[i] = "school_zone"
                break
    return out


def assign_zones(route: list[tuple[float, float]], seg_meta: list[tuple[str, str]]) -> list[RouteZone]:
    """One zone per segment; seg_meta[i] = (street_name, highway) for segment i."""
    zones: list[RouteZone] = []
    for i in range(len(route) - 1):
        p0, p1 = route[i], route[i + 1]
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        name, highway = seg_meta[i] if i < len(seg_meta) else ("", "unclassified")
        zone = _base_zone(name, highway, mid)
        if 0 < i + 1 < len(route) - 1:
            angle = turn_angle(route[i], route[i + 1], route[i + 2])
            if angle >= INTERSECTION_ANGLE:
                zone = "intersection"
        zones.append(zone)
    return boost_school_zones(route, zones)


def count_turns(route: list[tuple[float, float]], threshold: float = TURN_COUNT_THRESHOLD) -> int:
    n = 0
    for i in range(1, len(route) - 1):
        if turn_angle(route[i - 1], route[i], route[i + 1]) >= threshold:
            n += 1
    return n


def chain_segments(
    start: OsmSegment,
    pool: list[OsmSegment],
    *,
    max_extra: int = 8,
    gap_m: float = 40.0,
) -> tuple[list[tuple[float, float]], list[tuple[str, str]]]:
    route = list(start.points)
    meta: list[tuple[str, str]] = [(start.name, start.highway)] * (len(start.points) - 1)
    used = {start.id}
    tail = route[-1]

    for _ in range(max_extra):
        best: OsmSegment | None = None
        best_pts: list[tuple[float, float]] | None = None
        best_gap = gap_m
        best_score = float("inf")
        for seg in pool:
            if seg.id in used:
                continue
            for forward, pt in ((True, seg.points[0]), (False, seg.points[-1])):
                d = haversine_m(tail[0], tail[1], pt[0], pt[1])
                if d > gap_m:
                    continue
                cand = seg.points if forward else list(reversed(seg.points))
                angle = 0.0
                if len(route) >= 2 and len(cand) >= 2:
                    join = cand[1] if d < 12 else cand[0]
                    angle = turn_angle(route[-2], route[-1], join)
                score = d - min(angle, 90.0) * 1.8
                if score < best_score:
                    best_score = score
                    best_gap = d
                    best = seg
                    best_pts = cand
        if not best or not best_pts:
            break
        used.add(best.id)
        if best_gap < 12:
            attach = best_pts[1:]
        else:
            attach = best_pts
        route.extend(attach)
        meta.extend([(best.name, best.highway)] * len(attach))
        tail = route[-1]

    # Align metadata with segment count
    needed = len(route) - 1
    meta = meta[:needed]
    while len(meta) < needed:
        meta.append(meta[-1] if meta else ("", "unclassified"))

    return route, meta


def longest_for_street(segments: list[OsmSegment], street: str, exclude: set[int]) -> OsmSegment | None:
    cands = [s for s in segments if s.name == street and s.id not in exclude]
    return max(cands, key=lambda s: s.length) if cands else None


def pick_routes(segments: list[OsmSegment]) -> tuple[list[list[tuple[float, float]]], list[list[RouteZone]], list[str]]:
    used: set[int] = set()
    routes: list[list[tuple[float, float]]] = []
    all_zones: list[list[RouteZone]] = []
    names: list[str] = []

    def take_seg(seg: OsmSegment) -> None:
        used.add(seg.id)
        zones = assign_zones(seg.points, [(seg.name, seg.highway)] * (len(seg.points) - 1))
        routes.append(seg.points)
        all_zones.append(zones)
        names.append(_route_name(seg.name, zones, seg.points))

    def take_chain(start_street: str, max_extra: int, label: str) -> None:
        start = longest_for_street(segments, start_street, used)
        if not start:
            return
        used.add(start.id)
        pool = [s for s in segments if s.id not in used]
        route, meta = chain_segments(start, pool, max_extra=max_extra, gap_m=45.0)
        for s in segments:
            if s.id in used:
                continue
            if any(abs(s.points[0][0] - route[0][0]) < 1e-6 for _ in [1]):
                pass
        for s in pool:
            if s.points == route[: len(s.points)] or s.points == route:
                used.add(s.id)
        zones = assign_zones(route, meta)
        routes.append(route)
        all_zones.append(zones)
        names.append(label)

    # BASIC — single arterials (still real OSM, mild curves)
    for street, label in [
        ("El Camino Real", "El Camino Express"),
        ("Veterans Boulevard", "Veterans Highway"),
        ("Broadway", "Broadway Arterial"),
        ("Middlefield Road", "Middlefield Corridor"),
        ("Woodside Road", "Woodside Connector"),
    ]:
        seg = longest_for_street(segments, street, used)
        if seg:
            take_seg(seg)

    # MODERATE — 3–4 street chains, mixed zones
    moderate_chains = [
        ("Jefferson Avenue", 3, "Jefferson to Main Loop"),
        ("Marshall Street", 3, "Marshall Downtown Cut"),
        ("Maple Street", 4, "Maple-Spring Zigzag"),
        ("Bay Road", 4, "Bay Rd School Run"),
        ("Arguello Street", 4, "Arguello Hill Climb"),
    ]
    for street, extra, label in moderate_chains:
        if len(routes) >= 10:
            break
        start = longest_for_street(segments, street, used)
        if not start:
            continue
        used.add(start.id)
        pool = [s for s in segments if s.id not in used]
        route, meta = chain_segments(start, pool, max_extra=extra, gap_m=42.0)
        zones = assign_zones(route, meta)
        routes.append(route)
        all_zones.append(zones)
        names.append(label)

    # COMPLEX — long multi-street labyrinths, many turns + school + highway
    complex_chains = [
        ("Walnut Street", 9, "Walnut Hwy School Maze"),
        ("Laurel Street", 10, "Laurel Freeway Weave"),
        ("Spring Street", 9, "Spring Grid Labyrinth"),
        ("Bradford Street", 8, "Bradford Turn Storm"),
        ("Main Street", 10, "Main St Full Circuit"),
    ]
    for street, extra, label in complex_chains:
        if len(routes) >= 15:
            break
        start = longest_for_street(segments, street, used)
        if not start:
            continue
        used.add(start.id)
        pool = [s for s in segments if s.id not in used]
        route, meta = chain_segments(start, pool, max_extra=extra, gap_m=50.0)
        if len(route) < 12 and street == "Main Street":
            alt = longest_for_street(segments, "Jefferson Avenue", used)
            if alt:
                used.add(alt.id)
                pool2 = [s for s in segments if s.id not in used]
                route, meta = chain_segments(alt, pool2, max_extra=10, gap_m=55.0)
                label = "Jefferson Full Circuit"
        zones = assign_zones(route, meta)
        routes.append(route)
        all_zones.append(zones)
        names.append(label)

    while len(routes) < 15:
        for seg in segments:
            if seg.id not in used:
                used.add(seg.id)
                pool = [s for s in segments if s.id not in used]
                route, meta = chain_segments(seg, pool, max_extra=6, gap_m=55.0)
                zones = assign_zones(route, meta)
                routes.append(route)
                all_zones.append(zones)
                names.append(_route_name(seg.name, zones, route))
                break
        else:
            break

    return routes[:15], all_zones[:15], names[:15]


def _route_name(fallback: str, zones: list[RouteZone], route: list[tuple[float, float]]) -> str:
    turns = count_turns(route)
    parts = [fallback]
    if zones.count("highway") >= 2:
        parts.append("Hwy")
    if zones.count("school_zone") >= 1:
        parts.append("School")
    if turns >= 8:
        parts.append(f"{turns} turns")
    return " · ".join(parts) if len(parts) > 1 else fallback


def feature_tags(zones: list[RouteZone], route: list[tuple[float, float]]) -> list[str]:
    turns = count_turns(route)
    tags: list[str] = []
    hw = zones.count("highway")
    sz = zones.count("school_zone")
    ix = zones.count("intersection")
    if hw:
        tags.append(f"Highway ×{hw}")
    if sz:
        tags.append(f"School zone ×{sz}")
    if ix:
        tags.append(f"Intersections ×{ix}")
    tags.append(f"{turns} turns")
    tags.append(f"{len(route)-1} segments")
    return tags


def format_coords(route: list[tuple[float, float]]) -> list[str]:
    lines: list[str] = []
    chunk: list[str] = []
    for lat, lng in route:
        chunk.append(f"({lat:.6f}, {lng:.6f})")
        if len(chunk) == 4:
            lines.append("        " + ", ".join(chunk) + ",")
            chunk = []
    if chunk:
        lines.append("        " + ", ".join(chunk) + ",")
    return lines


def format_zones(zones: list[RouteZone]) -> str:
    return ", ".join(f'"{z}"' for z in zones)


def write_street_routes_data(
    routes: list[list[tuple[float, float]]],
    zones_list: list[list[RouteZone]],
    names: list[str],
) -> None:
    diffs = ["basic"] * 5 + ["moderate"] * 5 + ["complex"] * 5
    comments = [
        "car-001 · BASIC",
        "car-002 · BASIC",
        "car-003 · BASIC",
        "car-004 · BASIC",
        "car-005 · BASIC",
        "car-006 · MODERATE",
        "car-007 · MODERATE",
        "car-008 · MODERATE",
        "car-009 · MODERATE",
        "car-010 · MODERATE",
        "car-011 · COMPLEX",
        "car-012 · COMPLEX",
        "car-013 · COMPLEX",
        "car-014 · COMPLEX",
        "car-015 · COMPLEX",
    ]

    wp_lines = ["_ROUTE_WAYPOINTS: list[list[tuple[float, float]]] = ["]
    z_lines = ["_ROUTE_ZONES: list[list[RouteZone]] = ["]
    f_lines = ["ROUTE_FEATURES: list[list[str]] = ["]

    for idx, route in enumerate(routes):
        wp_lines.append(f"    # {comments[idx]} · {names[idx]}")
        wp_lines.append("    [")
        wp_lines.extend(format_coords(route))
        wp_lines.append("    ],")

        z = zones_list[idx]
        z_lines.append(f"    # {names[idx]} — {count_turns(route)} turns")
        z_lines.append(f"    [{format_zones(z)}],")

        feats = feature_tags(z, route)
        f_lines.append(f"    {feats!r},")

    wp_lines.append("]")
    z_lines.append("]")
    f_lines.append("]")

    content = f'''"""
Redwood City, CA — 15 OSM-snapped routes with zone metadata.

Zones: highway, arterial, residential, school_zone, intersection.
Coordinates from OpenStreetMap (rwc_osm.json).
"""

from __future__ import annotations

from typing import Literal

RouteDifficulty = Literal["basic", "moderate", "complex"]
RouteZone = Literal["highway", "arterial", "residential", "school_zone", "intersection"]

CITY_NAME = "Redwood City, CA"
MAP_CENTER = {{"lat": 37.4865, "lng": -122.2320, "zoom": 14}}

{chr(10).join(wp_lines)}

{chr(10).join(z_lines)}

{chr(10).join(f_lines)}

_ROUTE_DIFFICULTIES: list[RouteDifficulty] = (
    {diffs!r}
)

_ROUTE_NAMES: list[str] = {names!r}

URBAN_ROUTES: list[list[tuple[float, float]]] = _ROUTE_WAYPOINTS
ROUTE_ZONES: list[list[RouteZone]] = _ROUTE_ZONES
ROUTE_DIFFICULTIES: list[RouteDifficulty] = _ROUTE_DIFFICULTIES
ROUTE_NAMES: list[str] = _ROUTE_NAMES
'''
    TARGET.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    segments = load_segments()
    routes, zones_list, names = pick_routes(segments)
    write_street_routes_data(routes, zones_list, names)
    diffs = ["basic", "basic", "basic", "basic", "basic",
             "moderate", "moderate", "moderate", "moderate", "moderate",
             "complex", "complex", "complex", "complex", "complex"]
    for i, (route, zones, name) in enumerate(zip(routes, zones_list, names), 1):
        diff = diffs[i - 1]
        print(
            f"car-{i:03d} [{diff}] {name}: {len(route)} pts, {poly_length(route):.0f}m, "
            f"{count_turns(route)} turns, zones={{{', '.join(f'{z}:{zones.count(z)}' for z in sorted(set(zones)))}}}"
        )
