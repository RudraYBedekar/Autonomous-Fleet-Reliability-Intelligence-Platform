"""
Pydantic data models for DataHub MCP Server integration & FleetGuard context payload.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class DataHubStatusResponse(BaseModel):
    """Health status schema for DataHub GMS & MCP Server connection."""

    mcp_enabled: bool = Field(..., description="Whether DataHub MCP integration is enabled.")
    mcp_connected: bool = Field(..., description="Whether official mcp-server-datahub process is reachable.")
    datahub_connected: bool = Field(..., description="Whether DataHub GMS backend is reachable.")
    datahub_gms_url: str = Field(..., description="Configured DataHub GMS endpoint URL.")
    error: str | None = Field(default=None, description="Sanitized connection error message if unreachable.")


class NormalizedAssetContext(BaseModel):
    """Normalized metadata structure for DataHub entities."""

    asset: str = Field(..., description="Target asset urn or name.")
    description: str | None = Field(default=None, description="Asset documentation or description.")
    owners: list[str] = Field(default_factory=list, description="List of asset owner corpuser URNs or names.")
    schema_fields: list[dict[str, Any]] = Field(default_factory=list, description="Schema field definitions.")
    upstream: list[dict[str, Any]] = Field(default_factory=list, description="Upstream lineage dependencies.")
    downstream: list[dict[str, Any]] = Field(default_factory=list, description="Downstream lineage impact.")


class FleetGuardContextPayload(BaseModel):
    """Prepared DataHub metadata context payload for AWS Bedrock orchestration."""

    model_config = {"populate_by_name": True}

    asset: str = Field(..., description="Target asset name.")
    schema_fields: list[dict[str, Any]] = Field(default_factory=list, alias="schema", description="Schema fields.")
    upstream: list[dict[str, Any]] = Field(default_factory=list, description="Upstream dependencies.")
    downstream: list[dict[str, Any]] = Field(default_factory=list, description="Downstream dependencies.")
    affected_models: list[str] = Field(default_factory=list, description="Downstream ML models or features impacted.")
    owner: str | None = Field(default=None, description="Primary asset owner.")
    description: str | None = Field(default=None, description="Asset description.")
