"""
DataHub Context Service for FleetGuard AI.

Provides high-level data orchestration methods calling official DataHub MCP Server:
- search_assets(query)
- get_asset_context(asset_name)
- get_asset_schema(asset_name)
- get_asset_lineage(asset_name)
- get_downstream_impact(asset_name)
- get_asset_owner(asset_name)
- get_fleetguard_context(asset_name)
- get_status()

Returns normalized JSON schemas without faking DataHub metadata.
"""

from __future__ import annotations

from typing import Any
from backend.datahub.mcp_client import get_mcp_client
from backend.datahub.models import DataHubStatusResponse, FleetGuardContextPayload, NormalizedAssetContext


def get_status() -> DataHubStatusResponse:
    """Returns connection and configuration health for DataHub GMS backend & MCP Server."""
    client = get_mcp_client()
    if not client.is_enabled():
        return DataHubStatusResponse(
            mcp_enabled=False,
            mcp_connected=False,
            datahub_connected=False,
            datahub_gms_url=client.gms_url,
            error="DataHub MCP integration disabled via DATAHUB_MCP_ENABLED=false",
        )

    datahub_connected, mcp_connected, error = client.check_status()
    return DataHubStatusResponse(
        mcp_enabled=True,
        mcp_connected=mcp_connected,
        datahub_connected=datahub_connected,
        datahub_gms_url=client.gms_url,
        error=error,
    )


def search_assets(query: str) -> list[dict[str, Any]]:
    """Searches DataHub entities via official mcp-server-datahub search tool."""
    client = get_mcp_client()
    if not client.is_enabled():
        return []

    res = client.call_tool("search", {"query": query})
    if res.get("success") and isinstance(res.get("data"), list):
        return res["data"]
    return []


def get_asset_schema(asset_name: str) -> list[dict[str, Any]]:
    """Retrieves list of schema fields for asset_name from DataHub MCP."""
    client = get_mcp_client()
    if not client.is_enabled():
        return []

    res = client.call_tool("get_schema", {"asset_name": asset_name})
    if res.get("success") and isinstance(res.get("data"), list):
        return res["data"]
    return []


def get_asset_lineage(asset_name: str) -> dict[str, list[dict[str, Any]]]:
    """Retrieves upstream and downstream lineage graph for asset_name."""
    client = get_mcp_client()
    if not client.is_enabled():
        return {"upstream": [], "downstream": []}

    res = client.call_tool("get_lineage", {"asset_name": asset_name})
    if res.get("success") and isinstance(res.get("data"), dict):
        return {
            "upstream": res["data"].get("upstream", []),
            "downstream": res["data"].get("downstream", []),
        }
    return {"upstream": [], "downstream": []}


def get_downstream_impact(asset_name: str) -> list[dict[str, Any]]:
    """Retrieves downstream assets or models impacted by asset_name."""
    lineage = get_asset_lineage(asset_name)
    return lineage.get("downstream", [])


def get_asset_owner(asset_name: str) -> list[str]:
    """Retrieves list of owner corpuser URNs for asset_name."""
    client = get_mcp_client()
    if not client.is_enabled():
        return []

    res = client.call_tool("get_entity", {"asset_name": asset_name})
    if res.get("success") and isinstance(res.get("data"), dict):
        return res["data"].get("owners", [])
    return []


def get_asset_context(asset_name: str) -> NormalizedAssetContext:
    """
    Returns normalized DataHub asset metadata.
    Does NOT fake data if DataHub MCP is offline or entity does not exist.
    """
    schema = get_asset_schema(asset_name)
    lineage = get_asset_lineage(asset_name)
    owners = get_asset_owner(asset_name)

    return NormalizedAssetContext(
        asset=asset_name,
        description=None,
        owners=owners,
        schema_fields=schema,
        upstream=lineage.get("upstream", []),
        downstream=lineage.get("downstream", []),
    )


def get_fleetguard_context(asset_name: str) -> FleetGuardContextPayload:
    """
    Collects DataHub metadata payload prepared for future AWS Bedrock LLM context injection.
    Exposes: asset, schema, upstream, downstream, affected_models, owner, description.
    """
    ctx = get_asset_context(asset_name)
    affected_models = [
        item.get("urn", "")
        for item in ctx.downstream
        if "model" in item.get("urn", "").lower() or "prediction" in item.get("urn", "").lower()
    ]
    primary_owner = ctx.owners[0] if ctx.owners else None

    return FleetGuardContextPayload(
        asset=asset_name,
        schema=ctx.schema_fields,
        upstream=ctx.upstream,
        downstream=ctx.downstream,
        affected_models=affected_models,
        owner=primary_owner,
        description=ctx.description,
    )
