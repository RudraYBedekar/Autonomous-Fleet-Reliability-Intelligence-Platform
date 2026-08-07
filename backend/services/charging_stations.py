"""EV charging stations — Redwood City fleet network."""

from __future__ import annotations

from dataclasses import dataclass

from backend.services.routes import haversine_m

BATTERY_CRITICAL_PCT = 15.0
BATTERY_RESTORE_PCT = 80.0
CHARGE_RATE_AT_STATION = 0.08  # % per tick (~10 Hz) — fast DC charge
CHARGE_RATE_IDLE = 0.004


@dataclass(frozen=True)
class ChargingStation:
    station_id: str
    name: str
    address: str
    lat: float
    lng: float
    stalls: int = 4


# Redwood City public + fleet depot chargers
CHARGING_STATIONS: list[ChargingStation] = [
    ChargingStation(
        "rwc-caltrain",
        "Caltrain EV Hub",
        "2650 Broadway, Redwood City, CA 94063",
        37.4857,
        -122.2322,
        stalls=8,
    ),
    ChargingStation(
        "rwc-kaiser",
        "Kaiser Permanente EV",
        "1150 Veterans Blvd, Redwood City, CA 94063",
        37.4915,
        -122.2395,
        stalls=6,
    ),
    ChargingStation(
        "rwc-edison",
        "Edison Way Fleet Depot",
        "3505 Edison Way, Redwood City, CA 94063",
        37.4910,
        -122.2290,
        stalls=10,
    ),
    ChargingStation(
        "rwc-elcamino",
        "El Camino Real ChargePoint",
        "1201 El Camino Real, Redwood City, CA 94063",
        37.4900,
        -122.2348,
        stalls=4,
    ),
    ChargingStation(
        "rwc-shores",
        "Redwood Shores EV Plaza",
        "Redwood Shores Pkwy & Marine Pkwy, Redwood City, CA 94065",
        37.4920,
        -122.2295,
        stalls=6,
    ),
]


def nearest_station(lat: float, lng: float) -> ChargingStation:
    return min(
        CHARGING_STATIONS,
        key=lambda s: haversine_m(lat, lng, s.lat, s.lng),
    )


def station_to_dict(station: ChargingStation) -> dict:
    return {
        "station_id": station.station_id,
        "name": station.name,
        "address": station.address,
        "lat": station.lat,
        "lng": station.lng,
        "stalls": station.stalls,
    }


def all_stations() -> list[dict]:
    return [station_to_dict(s) for s in CHARGING_STATIONS]
