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
    metadata_source: str = Field(default="live", description="Source of metadata: 'live' or 'fallback'.")
    datahub_live: bool = Field(default=True, description="True if fetched live from DataHub GMS.")
    fallback_used: bool = Field(default=False, description="True if demo fallback was injected.")


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
    metadata_source: str = Field(default="live", description="Metadata origin: 'live' or 'fallback'.")
    datahub_live: bool = Field(default=True, description="Whether live DataHub GMS was read.")
    fallback_used: bool = Field(default=False, description="Whether fallback metadata was used.")


class InvestigationRecord(BaseModel):
    """Structured record of an AI agent vehicle investigation."""

    investigation_id: str = Field(..., description="Unique investigation identifier.")
    vehicle_id: str = Field(..., description="Target vehicle ID.")
    timestamp: str = Field(..., description="ISO timestamp of investigation.")
    severity: str = Field(..., description="Alert severity level.")
    root_cause: str = Field(..., description="Root cause summary.")
    affected_models: list[str] = Field(default_factory=list, description="Downstream ML models impacted.")
    action_taken: str = Field(..., description="Mitigation action executed.")
    datahub_written: bool = Field(..., description="Whether written back to DataHub GMS.")
    metadata_source: str = Field(default="live", description="Metadata origin ('live' | 'fallback').")

