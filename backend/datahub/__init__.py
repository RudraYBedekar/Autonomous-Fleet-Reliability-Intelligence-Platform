"""Official DataHub MCP Server Integration Package."""

from backend.datahub.context_service import (
    get_asset_context,
    get_asset_lineage,
    get_asset_owner,
    get_asset_schema,
    get_downstream_impact,
    get_fleetguard_context,
    get_status,
    search_assets,
)
from backend.datahub.mcp_client import DataHubMCPClient, get_mcp_client
from backend.datahub.models import DataHubStatusResponse, FleetGuardContextPayload, NormalizedAssetContext

__all__ = [
    "DataHubMCPClient",
    "get_mcp_client",
    "get_status",
    "search_assets",
    "get_asset_context",
    "get_asset_schema",
    "get_asset_lineage",
    "get_downstream_impact",
    "get_asset_owner",
    "get_fleetguard_context",
    "DataHubStatusResponse",
    "NormalizedAssetContext",
    "FleetGuardContextPayload",
]
