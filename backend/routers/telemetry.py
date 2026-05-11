from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
import datetime

from ..database.db import get_db
from ..database.models import TelemetryRecord

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

@router.get("/fleet-status")
def get_fleet_status(db: Session = Depends(get_db)):
    """Returns overall fleet health metrics."""
    # Count active critical alerts in the last 10 minutes
    ten_mins_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
    
    # Count vehicles
    vehicles = db.query(TelemetryRecord.vehicle_id).filter(TelemetryRecord.timestamp >= ten_mins_ago).distinct().count()
    
    alerts = db.query(TelemetryRecord).filter(
        TelemetryRecord.status == "Critical",
        TelemetryRecord.timestamp >= ten_mins_ago
    ).count()
    
    # Avg fleet health score based on anomalies
    total_recent = db.query(TelemetryRecord).filter(TelemetryRecord.timestamp >= ten_mins_ago).count()
    health_score = 100
    if total_recent > 0:
        health_score = max(0, 100 - (alerts / total_recent) * 100)
    
    return {
        "active_vehicles": vehicles,
        "critical_alerts": alerts,
        "fleet_health_score": round(health_score, 1)
    }

@router.get("/vehicles")
def get_vehicles(db: Session = Depends(get_db)):
    """List all vehicles."""
    results = db.query(TelemetryRecord.vehicle_id).distinct().all()
    return [r[0] for r in results]

@router.get("/history/{vehicle_id}")
def get_vehicle_history(vehicle_id: str, limit: int = 1000, db: Session = Depends(get_db)):
    """Get historical data for a specific vehicle."""
    records = db.query(TelemetryRecord).filter(
        TelemetryRecord.vehicle_id == vehicle_id
    ).order_by(TelemetryRecord.timestamp.desc()).limit(limit).all()
    return records

@router.get("/anomalies")
def get_recent_anomalies(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent anomalies across the fleet."""
    records = db.query(TelemetryRecord).filter(
        TelemetryRecord.status == "Critical"
    ).order_by(TelemetryRecord.timestamp.desc()).limit(limit).all()
    return records
