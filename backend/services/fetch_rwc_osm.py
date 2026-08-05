"""One-off helper: fetch Redwood City street geometry from OpenStreetMap."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

OVERPASS = "https://overpass-api.de/api/interpreter"

QUERY = """
[out:json][timeout:90];
(
  way["highway"]["name"~"El Camino Real",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Broadway",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Main Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Middlefield Road",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Veterans Boulevard",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Jefferson Avenue",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Marshall Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Bay Road",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Woodside Road",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Maple Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Laurel Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Arguello Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Bradford Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Spring Street",i](37.475,-122.252,37.502,-122.218);
  way["highway"]["name"~"Walnut Street",i](37.475,-122.252,37.502,-122.218);
);
out geom;
"""


def main() -> None:
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    req = urllib.request.Request(
        OVERPASS,
        data=data,
        headers={"User-Agent": "TelemetryProject/1.0 (local dev)", "Accept": "*/*"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        obj = json.load(resp)

    out_path = __file__.replace("fetch_rwc_osm.py", "rwc_osm.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f)

    by_name: dict[str, list] = {}
    for el in obj.get("elements", []):
        name = el.get("tags", {}).get("name", "?")
        geom = [(p["lat"], p["lon"]) for p in el.get("geometry", [])]
        by_name.setdefault(name, []).append(geom)

    print(f"Saved {len(obj.get('elements', []))} ways to {out_path}")
    for name, segments in sorted(by_name.items()):
        pts = sum(len(s) for s in segments)
        print(f"  {name}: {len(segments)} segment(s), {pts} points")


if __name__ == "__main__":
    main()
