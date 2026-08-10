"""
FleetGuard Router: API Endpoints for Autonomous AI Agent Loop.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.fleetguard_agent import fleetguard_agent

from backend.datahub.writeback import get_investigation_history

router = APIRouter(prefix="/api/fleetguard", tags=["FleetGuard Autonomous Agent"])


class AutonomousInvestigationRequest(BaseModel):
    vehicle_id: str = "car-001"
    alert_type: Optional[str] = None
    incident_type: Optional[str] = None


@router.post("/investigate")
def run_autonomous_investigation(payload: AutonomousInvestigationRequest) -> Dict[str, Any]:
    """
    Triggers the end-to-end 5-stage Autonomous AI Agent Investigation Loop:
    1. Alert Ingestion
    2. DataHub MCP Metadata & Lineage Retrieval
    3. AI Reasoning & Blast Radius Calculation
    4. Safe Mitigation Action Execution
    5. DataHub Write-Back Persistence
    """
    try:
        active_alert = payload.alert_type
        if payload.incident_type == "schema_drift" and not active_alert:
            active_alert = "SCHEMA_DRIFT_ALERT: Field 'battery_temperature' renamed/missing"

        result = fleetguard_agent.run_investigation(
            vehicle_id=payload.vehicle_id,
            alert_type=active_alert,
        )
        return result
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Autonomous investigation loop failed: {str(err)}")


@router.get("/investigations/{vehicle_id}")
def get_vehicle_investigation_history(vehicle_id: str) -> Dict[str, Any]:
    """Returns past AI agent investigation records for target vehicle."""
    records = get_investigation_history(vehicle_id)
    return {
        "vehicle_id": vehicle_id,
        "count": len(records),
        "investigations": records,
    }


@router.get("/investigations")
def get_all_investigation_history() -> Dict[str, Any]:
    """Returns all past AI agent investigation records across fleet."""
    records = get_investigation_history()
    return {
        "count": len(records),
        "investigations": records,
    }


@router.get("/status")
def get_fleetguard_agent_status() -> Dict[str, Any]:
    """Returns status and readiness of the FleetGuard Autonomous AI Agent loop."""
    return {
        "agent_name": "FleetGuard Autonomous Reliability Agent",
        "version": "2.0.0",
        "status": "READY",
        "capabilities": [
            "Real-time alert ingestion",
            "DataHub MCP & SDK context injection",
            "Downstream ML model blast radius calculation",
            "Schema drift anomaly detection",
            "AWS Bedrock multi-model LLM reasoning",
            "Autonomous vehicle reroute & mitigation dispatch",
            "DataHub GMS write-back persistence",
        ],
    }

