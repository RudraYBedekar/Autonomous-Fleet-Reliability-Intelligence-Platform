"""Schemas for fleet dispatch communication (call / passenger message)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PassengerMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class DispatchActionResponse(BaseModel):
    vehicle_id: str
    action: Literal["call", "message"]
    status: Literal["queued", "delivered"]
    timestamp: datetime
    detail: str
