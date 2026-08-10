"""
DataHub MCP FastAPI Router.

Provides health checks, normalized metadata lookup, and FleetGuard AI context endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from backend.datahub.context_service import (
    get_asset_context,
    get_fleetguard_context,
    get_status,
)
from backend.datahub.models import (
    DataHubStatusResponse,
    FleetGuardContextPayload,
    NormalizedAssetContext,
)

from pydantic import BaseModel
from typing import Optional, List
from backend.datahub.writeback import emit_investigation_result

router = APIRouter(prefix="/api/datahub", tags=["DataHub MCP"])


class WritebackRequest(BaseModel):
    asset_name: str = "vehicle_health_features"
    severity: str = "CRITICAL"
    root_cause: str = "Thermal runaway risk"
    action_taken: str = "Rerouted vehicle to station"
    affected_models: Optional[List[str]] = None
    vehicle_id: str = "car-001"


@router.get("/status", response_model=DataHubStatusResponse)
def datahub_status():
    """
    Health endpoint checking DataHub MCP Server connection & DataHub Core GMS status.
    Sanitizes errors and never exposes authentication tokens.
    """
    try:
        return get_status()
    except Exception as e:
        return DataHubStatusResponse(
            mcp_enabled=True,
            mcp_connected=False,
            datahub_connected=False,
            datahub_gms_url="http://localhost:8080",
            error=f"Health check error: {str(e)}",
        )


@router.get("/asset/{asset_name}", response_model=NormalizedAssetContext)
def asset_context(asset_name: str):
    """Retrieves normalized DataHub entity schema, lineage, and ownership."""
    try:
        return get_asset_context(asset_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fleetguard-context/{asset_name}", response_model=FleetGuardContextPayload)
def fleetguard_context(asset_name: str):
    """
    Prepares DataHub metadata context payload for orchestration with AWS Bedrock LLM reasoning.
    """
    try:
        return get_fleetguard_context(asset_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from backend.datahub.live_publisher import publish_live_fleet_metadata


@router.post("/publish-live")
def trigger_publish_live():
    """
    Triggers live publishing of real vehicle telemetry datasets, schemas, and ML lineage directly to DataHub GMS.
    """
    try:
        return publish_live_fleet_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live publishing failed: {str(e)}")


