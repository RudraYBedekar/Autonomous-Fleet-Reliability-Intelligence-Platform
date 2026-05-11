from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..database.models import TelemetryRecord

router = APIRouter(prefix="/api/ai", tags=["AI Copilot"])

class QueryRequest(BaseModel):
    query: str

@router.post("/ask")
def ask_copilot(req: QueryRequest, db: Session = Depends(get_db)):
    try:
        # Get context from DB
        alerts = db.query(TelemetryRecord).filter(TelemetryRecord.status == "Critical").order_by(TelemetryRecord.timestamp.desc()).limit(10).all()
        
        context_str = "Recent Critical Alerts:\n"
        if not alerts:
            context_str += "None\n"
        for a in alerts:
            context_str += f"- Vehicle: {a.vehicle_id}, Sensor: {a.sensor_id}, Temp: {a.temperature_c}, Voltage: {a.voltage_v}, Vibration: {a.vibration_g}\n"
            
        return {"response": f"Mock AI Response: AI functionality has been disabled. Here is the current context based on your database:\n{context_str}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
