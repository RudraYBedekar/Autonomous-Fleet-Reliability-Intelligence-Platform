"""In-memory dispatch log for vehicle calls and passenger messages."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.services.fleet_manifest import get_vehicle_manifest

_log: list[dict] = []


def _vehicle_phone(vehicle_id: str) -> str:
    num = int(vehicle_id.split("-")[1])
    return f"+1650555{num:04d}"


def initiate_call(vehicle_id: str) -> dict:
    manifest = get_vehicle_manifest(vehicle_id)
    if not manifest:
        raise ValueError("Vehicle not found")

    phone = _vehicle_phone(vehicle_id)
    entry = {
        "vehicle_id": vehicle_id,
        "action": "call",
        "status": "queued",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "driver_name": manifest.driver_name,
        "phone": phone,
        "detail": f"Outbound call to {vehicle_id} ({manifest.driver_name}) at {phone}",
    }
    _log.append(entry)
    print(f"[Dispatch] {entry['detail']}")
    return entry


def send_passenger_message(vehicle_id: str, message: str) -> dict:
    manifest = get_vehicle_manifest(vehicle_id)
    if not manifest:
        raise ValueError("Vehicle not found")

    entry = {
        "vehicle_id": vehicle_id,
        "action": "message",
        "status": "delivered",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passenger_count": manifest.passenger_count,
        "message": message.strip(),
        "detail": (
            f"Message sent to {manifest.passenger_count} passenger(s) "
            f"on {vehicle_id}: {message.strip()[:80]}"
        ),
    }
    _log.append(entry)
    print(f"[Dispatch] {entry['detail']}")
    return entry


def log_dispatch_action(vehicle_id: str, action: str, detail: str) -> dict:
    entry = {
        "vehicle_id": vehicle_id,
        "action": action,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detail": detail,
    }
    _log.append(entry)
    print(f"[Dispatch Action] {detail}")
    return entry


def get_dispatch_log(limit: int = 50) -> list[dict]:
    return _log[-limit:]

