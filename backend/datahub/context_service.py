"""
DataHub Metadata & Agent Context Service.

Exposes hackathon metadata functions:
- get_asset_context(asset_name)
- get_lineage(asset_name)
- get_impacted_assets(asset_name)
- get_asset_owner(asset_name)
- get_status()

If DataHub MCP configuration is absent, returns an explicit
"DataHub MCP not configured" state. No fake or mock metadata is returned.
"""

from __future__ import annotations

from typing import Any

from backend.datahub.mcp_client import get_mcp_client


def _unconfigured_state(operation: str, asset_name: str | None = None) -> dict[str, Any]:
    """Standardized response when DataHub MCP server is not configured."""
    return {
        "status": "unconfigured",
        "configured": False,
        "operation": operation,
        "asset_name": asset_name,
        "message": (
            "DataHub MCP not configured. Please set DATAHUB_MCP_URL, DATAHUB_GMS_URL, "
            "or DATAHUB_MCP_STDIO_CMD environment variables."
        ),
    }


def get_status() -> dict[str, Any]:
    """Returns the current connection and configuration status of DataHub MCP."""
    client = get_mcp_client()
    if not client.is_configured():
        return {
            "status": "unconfigured",
            "configured": False,
            "message": "DataHub MCP not configured.",
            "mcp_url": client.mcp_url,
            "gms_url": client.gms_url,
        }
    return {
        "status": "ready",
        "configured": True,
        "message": "DataHub MCP configured.",
        "mcp_url": client.mcp_url,
        "gms_url": client.gms_url,
    }


def get_asset_context(asset_name: str) -> dict[str, Any]:
    """
    Retrieves entity schema, metadata, tags, and terms for a given asset from DataHub.
    Returns unconfigured status if DataHub MCP is not set up.
    """
    client = get_mcp_client()
    if not client.is_configured():
        return _unconfigured_state("get_asset_context", asset_name)

    res = client.call_mcp_tool("get_asset_context", {"asset_name": asset_name})
    if res.get("status") == "unconfigured":
        return _unconfigured_state("get_asset_context", asset_name)
    return res


def get_lineage(asset_name: str) -> dict[str, Any]:
    """
    Retrieves upstream hardware/data dependencies and downstream fleet route lineage.
    Returns unconfigured status if DataHub MCP is not set up.
    """
    client = get_mcp_client()
    if not client.is_configured():
        return _unconfigured_state("get_lineage", asset_name)

    res = client.call_mcp_tool("get_lineage", {"asset_name": asset_name})
    if res.get("status") == "unconfigured":
        return _unconfigured_state("get_lineage", asset_name)
    return res


def get_impacted_assets(asset_name: str) -> dict[str, Any]:
    """
    Retrieves downstream impacted assets, routes, or sensors if an anomaly occurs on asset_name.
    Returns unconfigured status if DataHub MCP is not set up.
    """
    client = get_mcp_client()
    if not client.is_configured():
        return _unconfigured_state("get_impacted_assets", asset_name)

    res = client.call_mcp_tool("get_impacted_assets", {"asset_name": asset_name})
    if res.get("status") == "unconfigured":
        return _unconfigured_state("get_impacted_assets", asset_name)
    return res


def get_asset_owner(asset_name: str) -> dict[str, Any]:
    """
    Retrieves entity ownership, maintainer corpusers, and technical contact info from DataHub.
    Returns unconfigured status if DataHub MCP is not set up.
    """
    client = get_mcp_client()
    if not client.is_configured():
        return _unconfigured_state("get_asset_owner", asset_name)

    res = client.call_mcp_tool("get_asset_owner", {"asset_name": asset_name})
    if res.get("status") == "unconfigured":
        return _unconfigured_state("get_asset_owner", asset_name)
    return res
