"""
DataHub Write-Back Service for FleetGuard AI.

Provides functionality to emit agent investigation results, incident tags, and 
structured metadata properties back to DataHub GMS via REST / Emitter API.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


def emit_investigation_result(
    asset_name: str = "vehicle_health_features",
    severity: str = "CRITICAL",
    root_cause: str = "Thermal runaway risk / Sensor drift",
    action_taken: str = "Rerouted vehicle to station & alerted dispatcher",
    affected_models: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Emits agent investigation findings back into DataHub GMS.
    Attempts live REST/emitter call first; returns structured result regardless.
    """
    gms_url = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")
    enabled = os.getenv("DATAHUB_MCP_ENABLED", "true").lower() in ("true", "1", "yes")

    tags = ["#fleetguard_investigated", f"#severity_{severity.lower()}", "#auto_mitigated"]
    properties = {
        "last_investigation_time": "2026-08-10T04:00:00Z",
        "severity": severity,
        "root_cause": root_cause,
        "action_taken": action_taken,
        "affected_models_count": str(len(affected_models or [])),
        "investigated_by": "FleetGuard Autonomous AI Agent",
    }

    payload = {
        "asset": asset_name,
        "tags": tags,
        "customProperties": properties,
        "affected_models": affected_models or ["urn:li:mlModel:(fleetguard,rul_predictor,PROD)", "urn:li:mlModel:(fleetguard,anomaly_detector,PROD)"],
    }

    if not enabled:
        logger.info("DataHub MCP disabled; write-back recorded in local payload mode.")
        return {
            "success": True,
            "datahub_written": False,
            "mode": "offline_payload",
            "details": payload,
        }

    # Attempt REST emission to DataHub GMS endpoint
    try:
        urn = f"urn:li:dataset:(urn:li:dataPlatform:kafka,{asset_name},PROD)"
        # Try direct GMS aspect post or tags update
        resp = httpx.post(
            f"{gms_url}/aspects?action=ingestProposal",
            json={
                "proposal": {
                    "entityType": "dataset",
                    "entityUrn": urn,
                    "aspectName": "datasetProperties",
                    "aspect": {
                        "json": json.dumps({
                            "name": asset_name,
                            "description": f"Real-time vehicle telemetry (Last AI Investigation: {root_cause})",
                            "customProperties": properties,
                        })
                    },
                }
            },
            timeout=3.0,
        )
        if resp.status_code in (200, 201):
            return {
                "success": True,
                "datahub_written": True,
                "mode": "gms_rest",
                "details": payload,
            }
    except Exception as e:
        logger.warning(f"Could not reach DataHub GMS for live write-back: {e}")

    # Fallback to python SDK if acryl-datahub installed
    try:
        from datahub.emitter.mcp import MetadataChangeProposalWrapper
        from datahub.ingestion.graph.client import DataHubGraph
        from datahub.ingestion.graph.config import DatahubClientConfig
        from datahub.metadata.schema_classes import DatasetPropertiesClass

        graph = DataHubGraph(DatahubClientConfig(server=gms_url))
        urn = f"urn:li:dataset:(urn:li:dataPlatform:kafka,{asset_name},PROD)"
        mcp = MetadataChangeProposalWrapper(
            entityType="dataset",
            entityUrn=urn,
            aspect=DatasetPropertiesClass(
                name=asset_name,
                description=f"Real-time vehicle telemetry (Last AI Agent Investigation: {root_cause})",
                customProperties=properties,
            ),
        )
        graph.emit(mcp)
        return {
            "success": True,
            "datahub_written": True,
            "mode": "datahub_graph_emitter",
            "details": payload,
        }
    except Exception as ex:
        logger.warning(f"DataHub Graph SDK emitter offline: {ex}")

    return {
        "success": True,
        "datahub_written": False,
        "mode": "agent_local_record",
        "details": payload,
    }
