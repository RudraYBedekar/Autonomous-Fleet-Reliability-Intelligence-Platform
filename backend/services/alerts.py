"""Rule-based fleet alerts from live telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.schemas.telemetry import VehicleTelemetry
from backend.services.charging_stations import BATTERY_CRITICAL_PCT

SCHOOL_ZONE_SPEED_LIMIT = 25.0


@dataclass
class FleetAlert:
    vehicle_id: str
    severity: str  # info | warning | critical
    code: str
    message: str
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


_active: list[FleetAlert] = []
_MAX_ALERTS = 80


def evaluate_alerts(
    point: VehicleTelemetry,
    *,
    idle_seconds: float = 0.0,
) -> list[FleetAlert]:
    alerts: list[FleetAlert] = []
    ts = point.timestamp if point.timestamp.tzinfo else point.timestamp.replace(tzinfo=timezone.utc)

    if point.battery_pct < BATTERY_CRITICAL_PCT:
        msg = f"{point.vehicle_id} battery critical ({point.battery_pct:.0f}%) — auto-routing to charger"
        if point.trip_status == "routing_to_charger" and point.charger_station_name:
            msg = f"{point.vehicle_id} low battery — routing to {point.charger_station_name}"
        elif point.trip_status == "charging" and point.charger_station_name:
            msg = f"{point.vehicle_id} charging at {point.charger_station_name} ({point.battery_pct:.0f}%)"
        alerts.append(FleetAlert(
            point.vehicle_id, "critical", "battery_critical", msg, ts,
        ))
    elif point.battery_pct < 25:
        alerts.append(FleetAlert(
            point.vehicle_id, "warning", "battery_low",
            f"{point.vehicle_id} battery low ({point.battery_pct:.0f}%)", ts,
        ))

    if point.health_score < 70:
        alerts.append(FleetAlert(
            point.vehicle_id, "critical", "health_critical",
            f"{point.vehicle_id} health degraded ({point.health_score:.0f}%)", ts,
        ))
    elif point.health_score < 80:
        alerts.append(FleetAlert(
            point.vehicle_id, "warning", "health_low",
            f"{point.vehicle_id} health watch ({point.health_score:.0f}%)", ts,
        ))

    if point.road_zone == "school_zone" and point.speed_kmh > SCHOOL_ZONE_SPEED_LIMIT + 3:
        alerts.append(FleetAlert(
            point.vehicle_id, "warning", "school_zone_speed",
            f"{point.vehicle_id} speeding in school zone ({point.speed_kmh:.0f} km/h)", ts,
        ))

    if idle_seconds >= 45 and 5 < point.trip_progress_pct < 95:
        alerts.append(FleetAlert(
            point.vehicle_id, "warning", "stalled_mid_route",
            f"{point.vehicle_id} stalled mid-route ({int(idle_seconds)}s idle)", ts,
        ))

    if point.maintenance_rul_pct < 20:
        alerts.append(FleetAlert(
            point.vehicle_id, "critical", "maintenance_due",
            f"{point.vehicle_id} maintenance due soon (RUL {point.maintenance_rul_pct:.0f}%)", ts,
        ))
    elif point.maintenance_rul_pct < 35:
        alerts.append(FleetAlert(
            point.vehicle_id, "warning", "maintenance_soon",
            f"{point.vehicle_id} schedule maintenance (RUL {point.maintenance_rul_pct:.0f}%)", ts,
        ))

    if point.trip_status == "delayed":
        eta_txt = f"{point.eta_minutes:.0f} min" if point.eta_minutes is not None else "unknown"
        alerts.append(FleetAlert(
            point.vehicle_id, "info", "trip_delayed",
            f"{point.vehicle_id} trip delayed — ETA {eta_txt}", ts,
        ))

    return alerts


def push_alerts(new_alerts: list[FleetAlert]) -> None:
    global _active
    for a in new_alerts:
        _active = [x for x in _active if not (x.vehicle_id == a.vehicle_id and x.code == a.code)]
        _active.append(a)
    _active = sorted(_active, key=lambda x: x.timestamp, reverse=True)[:_MAX_ALERTS]


def get_active_alerts(limit: int = 30) -> list[dict]:
    return [a.to_dict() for a in _active[:limit]]
