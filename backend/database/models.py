from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .db import Base
import datetime

class TelemetryRecord(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    vehicle_id = Column(String, index=True)
    sensor_id = Column(String, index=True)
    temperature_c = Column(Float)
    voltage_v = Column(Float)
    vibration_g = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String)
    
    # ML Fields
    ml_anomaly = Column(Boolean, default=False)
    predicted_rul_hours = Column(Float, nullable=True)
