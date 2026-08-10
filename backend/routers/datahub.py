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

router = APIRouter(prefix="/api/datahub", tags=["DataHub MCP"])


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
            datahub_gms_url="http://127.0.0.1:18080",
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
