from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.schemas.dispatch import DispatchActionResponse, PassengerMessageRequest
from backend.services.dispatch import get_dispatch_log, initiate_call, send_passenger_message
from backend.services.fleet_manifest import get_fleet_manifest, get_vehicle_manifest

router = APIRouter(prefix="/api/fleet", tags=["Fleet"])


@router.get("/manifest")
def fleet_manifest():
    """All vehicles with pickup, destination, route, and baseline health."""
    return [m.to_dict() for m in get_fleet_manifest()]


@router.get("/manifest/{vehicle_id}")
def vehicle_manifest(vehicle_id: str):
    manifest = get_vehicle_manifest(vehicle_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return manifest.to_dict()


@router.post("/{vehicle_id}/call", response_model=DispatchActionResponse)
def call_vehicle(vehicle_id: str):
    """Initiate a direct voice call to the vehicle / driver."""
    try:
        entry = initiate_call(vehicle_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return DispatchActionResponse(
        vehicle_id=entry["vehicle_id"],
        action="call",
        status=entry["status"],
        timestamp=datetime.fromisoformat(entry["timestamp"]),
        detail=entry["detail"],
    )


@router.post("/{vehicle_id}/message", response_model=DispatchActionResponse)
def message_passengers(vehicle_id: str, body: PassengerMessageRequest):
    """Send an in-cabin message to passengers on the vehicle."""
    try:
        entry = send_passenger_message(vehicle_id, body.message)
    except ValueError:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return DispatchActionResponse(
        vehicle_id=entry["vehicle_id"],
        action="message",
        status=entry["status"],
        timestamp=datetime.fromisoformat(entry["timestamp"]),
        detail=entry["detail"],
    )


@router.get("/dispatch-log")
def dispatch_log(limit: int = 50):
    return get_dispatch_log(limit)
