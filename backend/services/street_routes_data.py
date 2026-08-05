"""
Redwood City, CA — 15 OSM-snapped routes with zone metadata.

Zones: highway, arterial, residential, school_zone, intersection.
Coordinates from OpenStreetMap (rwc_osm.json).
"""

from __future__ import annotations

from typing import Literal

RouteDifficulty = Literal["basic", "moderate", "complex"]
RouteZone = Literal["highway", "arterial", "residential", "school_zone", "intersection"]

CITY_NAME = "Redwood City, CA"
MAP_CENTER = {"lat": 37.4865, "lng": -122.2320, "zoom": 14}

_ROUTE_WAYPOINTS: list[list[tuple[float, float]]] = [
    # car-001 · BASIC · El Camino Real · Hwy
    [
        (37.476584, -122.222096), (37.476032, -122.221332), (37.475689, -122.220850), (37.475671, -122.220826),
        (37.475426, -122.220491), (37.475153, -122.220111),
    ],
    # car-002 · BASIC · Veterans Boulevard · Hwy
    [
        (37.489735, -122.224790), (37.489705, -122.224555), (37.489544, -122.223284), (37.489517, -122.223059),
        (37.489476, -122.222718), (37.489444, -122.222464),
    ],
    # car-003 · BASIC · Broadway · Hwy
    [
        (37.486073, -122.237982), (37.486041, -122.238551), (37.486022, -122.238788), (37.486016, -122.238934),
        (37.486001, -122.239252), (37.485999, -122.239365), (37.485935, -122.240700),
    ],
    # car-004 · BASIC · Middlefield Road · Hwy
    [
        (37.483601, -122.224819), (37.483558, -122.224723), (37.483503, -122.224599), (37.483380, -122.224312),
        (37.483358, -122.224264), (37.483240, -122.223994), (37.483220, -122.223949), (37.482928, -122.223292),
        (37.482895, -122.223218), (37.482855, -122.223131), (37.482582, -122.222513), (37.482546, -122.222433),
        (37.482513, -122.222351),
    ],
    # car-005 · BASIC · Woodside Road · Hwy
    [
        (37.481108, -122.219013), (37.481203, -122.218946), (37.482824, -122.217814), (37.483001, -122.217659),
        (37.483151, -122.217522), (37.483321, -122.217325), (37.483464, -122.217119), (37.483600, -122.216896),
        (37.483981, -122.216204), (37.484140, -122.215911),
    ],
    # car-006 · MODERATE · Jefferson to Main Loop
    [
        (37.474907, -122.239088), (37.475209, -122.238814), (37.475507, -122.238560), (37.475853, -122.238249),
        (37.476204, -122.237908), (37.476853, -122.237165), (37.476977, -122.237092), (37.477487, -122.236527),
        (37.477539, -122.236469), (37.477234, -122.236660), (37.476931, -122.237016), (37.476853, -122.237165),
    ],
    # car-007 · MODERATE · Marshall Downtown Cut
    [
        (37.487663, -122.221413), (37.487670, -122.221261), (37.487673, -122.221214), (37.487694, -122.220738),
        (37.487703, -122.220537), (37.487713, -122.220332), (37.487718, -122.220200), (37.487728, -122.219996),
        (37.487737, -122.219787), (37.487750, -122.219499), (37.487761, -122.219265), (37.487769, -122.219089),
        (37.487777, -122.218911), (37.487785, -122.218742), (37.487797, -122.218462), (37.487808, -122.218231),
        (37.487809, -122.218200), (37.487816, -122.218050),
    ],
    # car-008 · MODERATE · Maple-Spring Zigzag
    [
        (37.484026, -122.225527), (37.484109, -122.225471), (37.484216, -122.225395), (37.484485, -122.225213),
        (37.484558, -122.225163), (37.484757, -122.225027), (37.484810, -122.224991), (37.484883, -122.224938),
        (37.485579, -122.224436), (37.485674, -122.224367), (37.485892, -122.224232), (37.486311, -122.223938),
        (37.486545, -122.223774), (37.486509, -122.223696), (37.486306, -122.223256), (37.486223, -122.223063),
        (37.486188, -122.222983), (37.486160, -122.222918), (37.485840, -122.222188), (37.485498, -122.221411),
        (37.485143, -122.220605), (37.485073, -122.220445), (37.484893, -122.220037), (37.484790, -122.219806),
        (37.484774, -122.219771), (37.484764, -122.219750), (37.484523, -122.218579), (37.484445, -122.218214),
        (37.484294, -122.217507), (37.484255, -122.217326), (37.484192, -122.217032), (37.484125, -122.216715),
    ],
    # car-009 · MODERATE · Bay Rd School Run
    [
        (37.485812, -122.218288), (37.485783, -122.218083), (37.485655, -122.217079), (37.485600, -122.216640),
        (37.485530, -122.215991), (37.485479, -122.215520), (37.485451, -122.215262), (37.485445, -122.215207),
    ],
    # car-010 · MODERATE · Arguello Hill Climb
    [
        (37.488186, -122.234678), (37.488262, -122.234763), (37.488764, -122.235322), (37.488871, -122.235446),
        (37.489276, -122.235913), (37.489332, -122.235978), (37.489645, -122.236326), (37.489908, -122.236619),
        (37.490324, -122.237077), (37.490493, -122.237262), (37.491055, -122.237909), (37.491292, -122.238194),
        (37.491545, -122.238496), (37.491611, -122.238576), (37.491696, -122.238672), (37.491840, -122.238836),
        (37.492152, -122.239204), (37.492664, -122.239801), (37.493173, -122.240376), (37.493677, -122.240921),
    ],
    # car-011 · COMPLEX · Walnut Hwy School Maze
    [
        (37.497574, -122.251949), (37.496604, -122.250815), (37.496471, -122.250492), (37.496426, -122.250400),
        (37.496376, -122.250323), (37.495855, -122.249716), (37.495443, -122.249252), (37.495375, -122.249176),
        (37.495323, -122.249116), (37.494562, -122.248245), (37.494501, -122.248175), (37.494458, -122.248126),
        (37.493703, -122.247267), (37.493639, -122.247194), (37.493586, -122.247135), (37.493565, -122.247110),
        (37.493167, -122.246648), (37.492720, -122.246122), (37.492704, -122.246103), (37.492663, -122.246054),
    ],
    # car-012 · COMPLEX · Laurel Freeway Weave
    [
        (37.498107, -122.251165), (37.498048, -122.251091), (37.498038, -122.251079), (37.497815, -122.250805),
        (37.497662, -122.250620), (37.497395, -122.250215), (37.497180, -122.249888), (37.497034, -122.249707),
        (37.496983, -122.249645), (37.496929, -122.249584), (37.496863, -122.249512), (37.496418, -122.248999),
        (37.496249, -122.248804), (37.496049, -122.248584), (37.495998, -122.248528), (37.495939, -122.248458),
        (37.495114, -122.247483), (37.495053, -122.247411), (37.495010, -122.247362), (37.494864, -122.247197),
        (37.494463, -122.246742), (37.494304, -122.246561), (37.494216, -122.246462), (37.494170, -122.246410),
        (37.494116, -122.246352), (37.494064, -122.246289), (37.493435, -122.245569), (37.493395, -122.245524),
        (37.493368, -122.245493), (37.493318, -122.245437),
    ],
    # car-013 · COMPLEX · Spring Grid Labyrinth
    [
        (37.486545, -122.223774), (37.486509, -122.223696), (37.486306, -122.223256), (37.486223, -122.223063),
        (37.486188, -122.222983), (37.486160, -122.222918), (37.485840, -122.222188), (37.485498, -122.221411),
        (37.485143, -122.220605), (37.485073, -122.220445), (37.484893, -122.220037), (37.484790, -122.219806),
        (37.484774, -122.219771), (37.484764, -122.219750), (37.484523, -122.218579), (37.484445, -122.218214),
        (37.484294, -122.217507), (37.484255, -122.217326), (37.484192, -122.217032), (37.484125, -122.216715),
        (37.484125, -122.216226), (37.483914, -122.216647), (37.483614, -122.217136), (37.483498, -122.217325),
        (37.483369, -122.217488), (37.483212, -122.217668), (37.483015, -122.217848), (37.482797, -122.218003),
        (37.481980, -122.218580), (37.481757, -122.218728),
    ],
    # car-014 · COMPLEX · Bradford Turn Storm
    [
        (37.488581, -122.229322), (37.488588, -122.229204), (37.488629, -122.228453), (37.488635, -122.228345),
        (37.488639, -122.228242), (37.488651, -122.227956), (37.488686, -122.227221), (37.488694, -122.227051),
        (37.488703, -122.226840), (37.488710, -122.226597), (37.488713, -122.226491), (37.488719, -122.226392),
        (37.488750, -122.225870), (37.488768, -122.225587), (37.488768, -122.225565), (37.488772, -122.225474),
        (37.488684, -122.225472), (37.488658, -122.225471), (37.488283, -122.225440), (37.487835, -122.225409),
        (37.487821, -122.225406), (37.487729, -122.225385), (37.487726, -122.225488), (37.487703, -122.226169),
        (37.487682, -122.226290), (37.487664, -122.226400), (37.487932, -122.226425), (37.488193, -122.226445),
        (37.488461, -122.226469), (37.488713, -122.226491), (37.488819, -122.226498), (37.489251, -122.226523),
    ],
    # car-015 · COMPLEX · Jefferson Full Circuit
    [
        (37.488105, -122.228309), (37.488153, -122.228312), (37.488235, -122.228315), (37.488546, -122.228339),
        (37.488635, -122.228345), (37.488718, -122.228352), (37.489082, -122.228378), (37.489199, -122.228387),
        (37.489306, -122.228395), (37.489545, -122.228414), (37.489666, -122.228423), (37.490018, -122.228450),
        (37.490201, -122.228463), (37.490230, -122.228460), (37.490322, -122.228455), (37.490285, -122.228296),
        (37.490263, -122.228202), (37.490212, -122.228009), (37.490165, -122.227825), (37.490111, -122.227589),
        (37.490300, -122.227836), (37.490281, -122.227753), (37.490232, -122.227505), (37.490217, -122.227430),
        (37.490185, -122.227269), (37.490141, -122.227024), (37.490106, -122.226800), (37.490098, -122.226740),
        (37.490084, -122.226635), (37.490161, -122.226648), (37.490182, -122.226651), (37.490343, -122.226678),
        (37.490560, -122.226768), (37.490729, -122.226884), (37.490763, -122.226909), (37.490932, -122.226900),
        (37.490557, -122.226612), (37.490522, -122.226602), (37.490318, -122.226539), (37.490137, -122.226510),
        (37.490111, -122.226506), (37.490066, -122.226499), (37.489955, -122.226635), (37.489972, -122.226756),
        (37.489974, -122.226774), (37.490000, -122.226963), (37.490030, -122.227157),
    ],
]

_ROUTE_ZONES: list[list[RouteZone]] = [
    # El Camino Real · Hwy — 0 turns
    ["highway", "highway", "highway", "highway", "highway"],
    # Veterans Boulevard · Hwy — 0 turns
    ["highway", "highway", "highway", "highway", "highway"],
    # Broadway · Hwy — 0 turns
    ["highway", "highway", "highway", "highway", "highway", "highway"],
    # Middlefield Road · Hwy — 0 turns
    ["highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway"],
    # Woodside Road · Hwy — 0 turns
    ["highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway"],
    # Jefferson to Main Loop — 4 turns
    ["highway", "highway", "highway", "highway", "highway", "highway", "highway", "intersection", "highway", "highway", "highway"],
    # Marshall Downtown Cut — 0 turns
    ["residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential"],
    # Maple-Spring Zigzag — 2 turns
    ["residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "intersection", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential"],
    # Bay Rd School Run — 0 turns
    ["arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial"],
    # Arguello Hill Climb — 0 turns
    ["residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential"],
    # Walnut Hwy School Maze — 1 turns
    ["intersection", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential"],
    # Laurel Freeway Weave — 0 turns
    ["arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial", "arterial"],
    # Spring Grid Labyrinth — 3 turns
    ["residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "intersection", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "highway"],
    # Bradford Turn Storm — 3 turns
    ["school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "residential", "residential", "residential", "residential", "residential", "residential", "residential", "intersection", "residential", "residential", "residential", "residential", "residential", "intersection", "residential", "school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "arterial", "arterial", "arterial"],
    # Jefferson Full Circuit — 9 turns
    ["school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "school_zone", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "intersection", "highway", "highway", "highway", "highway", "intersection", "intersection", "highway", "highway", "highway", "highway", "highway", "highway", "highway", "intersection", "arterial", "arterial", "arterial", "arterial", "arterial", "intersection", "intersection", "arterial", "arterial", "arterial", "arterial", "arterial", "intersection", "intersection", "highway", "highway", "highway", "highway"],
]

ROUTE_FEATURES: list[list[str]] = [
    ['Highway ×5', '0 turns', '5 segments'],
    ['Highway ×5', '0 turns', '5 segments'],
    ['Highway ×6', '0 turns', '6 segments'],
    ['Highway ×12', '0 turns', '12 segments'],
    ['Highway ×9', '0 turns', '9 segments'],
    ['Highway ×10', 'Intersections ×1', '4 turns', '11 segments'],
    ['0 turns', '17 segments'],
    ['Intersections ×1', '2 turns', '31 segments'],
    ['0 turns', '7 segments'],
    ['0 turns', '19 segments'],
    ['Intersections ×1', '1 turns', '19 segments'],
    ['0 turns', '29 segments'],
    ['Highway ×9', 'Intersections ×1', '3 turns', '29 segments'],
    ['School zone ×13', 'Intersections ×2', '3 turns', '31 segments'],
    ['Highway ×22', 'School zone ×6', 'Intersections ×8', '9 turns', '46 segments'],
]

_ROUTE_DIFFICULTIES: list[RouteDifficulty] = (
    ['basic', 'basic', 'basic', 'basic', 'basic', 'moderate', 'moderate', 'moderate', 'moderate', 'moderate', 'complex', 'complex', 'complex', 'complex', 'complex']
)

_ROUTE_NAMES: list[str] = ['El Camino Real · Hwy', 'Veterans Boulevard · Hwy', 'Broadway · Hwy', 'Middlefield Road · Hwy', 'Woodside Road · Hwy', 'Jefferson to Main Loop', 'Marshall Downtown Cut', 'Maple-Spring Zigzag', 'Bay Rd School Run', 'Arguello Hill Climb', 'Walnut Hwy School Maze', 'Laurel Freeway Weave', 'Spring Grid Labyrinth', 'Bradford Turn Storm', 'Jefferson Full Circuit']

URBAN_ROUTES: list[list[tuple[float, float]]] = _ROUTE_WAYPOINTS
ROUTE_ZONES: list[list[RouteZone]] = _ROUTE_ZONES
ROUTE_DIFFICULTIES: list[RouteDifficulty] = _ROUTE_DIFFICULTIES
ROUTE_NAMES: list[str] = _ROUTE_NAMES
