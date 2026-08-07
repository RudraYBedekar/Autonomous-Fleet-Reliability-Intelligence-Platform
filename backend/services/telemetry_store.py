"""In-memory telemetry ring buffer for route replay."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
from threading import Lock

from backend.schemas.telemetry import VehicleTelemetry

_HISTORY_SECONDS = 300  # 5 minutes
_SAMPLE_INTERVAL_S = 1.0

_buffers: dict[str, deque[dict]] = {}
_last_sample: dict[str, datetime] = {}
_lock = Lock()


def _point_dict(point: VehicleTelemetry) -> dict:
    return {
        "timestamp": point.timestamp.isoformat(),
        "lat": point.lat,
        "lng": point.lng,
        "speed_kmh": point.speed_kmh,
        "road_zone": point.road_zone,
        "trip_status": point.trip_status,
    }


def record(point: VehicleTelemetry) -> None:
    ts = point.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    with _lock:
        last = _last_sample.get(point.vehicle_id)
        if last and (ts - last).total_seconds() < _SAMPLE_INTERVAL_S:
            return

        buf = _buffers.setdefault(point.vehicle_id, deque(maxlen=_HISTORY_SECONDS))
        buf.append(_point_dict(point))
        _last_sample[point.vehicle_id] = ts


def get_history(vehicle_id: str, minutes: float = 5.0) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    with _lock:
        buf = _buffers.get(vehicle_id, deque())
        out = []
        for pt in buf:
            ts = datetime.fromisoformat(pt["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                out.append(pt)
        return out
