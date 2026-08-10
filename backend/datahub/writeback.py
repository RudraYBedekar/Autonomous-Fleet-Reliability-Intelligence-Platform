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
from datetime import datetime, timezone

# In-memory investigation history cache
INVESTIGATION_HISTORY: List[Dict[str, Any]] = []


def get_investigation_history(vehicle_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns investigation history filtered by vehicle_id if provided."""
    if vehicle_id:
        return [r for r in INVESTIGATION_HISTORY if r.get("vehicle_id") == vehicle_id]
    return list(INVESTIGATION_HISTORY)


def emit_investigation_result(
    asset_name: str = "vehicle_health_features",
    severity: str = "CRITICAL",
    root_cause: str = "Thermal runaway risk / Sensor drift",
    action_taken: str = "Rerouted vehicle to station & alerted dispatcher",
    affected_models: Optional[List[str]] = None,
    vehicle_id: str = "car-001",
) -> Dict[str, Any]:
    """
    Emits agent investigation findings back into DataHub GMS.
    Emits datasetProperties and globalTags aspects.
    Returns honest success and datahub_written flags.
    """
    gms_url = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")
    enabled = os.getenv("DATAHUB_MCP_ENABLED", "true").lower() in ("true", "1", "yes")
    now_iso = datetime.now(timezone.utc).isoformat()

    tags = ["fleetguard_investigated", f"severity_{severity.lower()}", "auto_mitigated"]
    properties = {
        "last_investigation_time": now_iso,
        "severity": severity,
        "root_cause": root_cause,
        "action_taken": action_taken,
        "affected_models_count": str(len(affected_models or [])),
        "investigated_by": "FleetGuard Autonomous AI Agent",
        "target_vehicle": vehicle_id,
    }

    payload = {
        "asset": asset_name,
        "vehicle_id": vehicle_id,
        "tags": [f"#{t}" for t in tags],
        "customProperties": properties,
        "affected_models": affected_models or [],
    }

    record = {
        "investigation_id": f"inv-{int(datetime.now().timestamp())}",
        "vehicle_id": vehicle_id,
        "timestamp": now_iso,
        "severity": severity,
        "root_cause": root_cause,
        "affected_models": affected_models or [],
        "action_taken": action_taken,
        "datahub_written": False,
        "mode": "offline",
    }

    if not enabled:
        logger.info("DataHub MCP disabled; write-back recorded locally.")
        record["mode"] = "offline_payload"
        INVESTIGATION_HISTORY.append(record)
        return {
            "success": False,
            "datahub_written": False,
            "mode": "offline_payload",
            "error": "DATAHUB_MCP_ENABLED is set to false",
            "details": payload,
        }

    urn = f"urn:li:dataset:(urn:li:dataPlatform:kafka,{asset_name},PROD)"

    # Method 1: Python SDK if acryl-datahub installed
    try:
        import importlib
        mcp_mod = importlib.import_module("datahub.emitter.mcp")
        graph_mod = importlib.import_module("datahub.ingestion.graph.client")
        config_mod = importlib.import_module("datahub.ingestion.graph.config")
        schema_mod = importlib.import_module("datahub.metadata.schema_classes")

        MetadataChangeProposalWrapper = getattr(mcp_mod, "MetadataChangeProposalWrapper")
        DataHubGraph = getattr(graph_mod, "DataHubGraph")
        DatahubClientConfig = getattr(config_mod, "DatahubClientConfig")
        DatasetPropertiesClass = getattr(schema_mod, "DatasetPropertiesClass")
        GlobalTagsClass = getattr(schema_mod, "GlobalTagsClass")
        TagAssociationClass = getattr(schema_mod, "TagAssociationClass")
        TagUrnClass = getattr(schema_mod, "TagUrnClass")

        graph = DataHubGraph(DatahubClientConfig(server=gms_url))
        mcp_props = MetadataChangeProposalWrapper(
            entityType="dataset",
            entityUrn=urn,
            aspect=DatasetPropertiesClass(
                name=asset_name,
                description=f"Real-time vehicle telemetry (Last AI Agent Investigation: {root_cause})",
                customProperties=properties,
            ),
        )
        graph.emit(mcp_props)

        tag_associations = [TagAssociationClass(tag=TagUrnClass.create_with_id(t)) for t in tags]
        mcp_tags = MetadataChangeProposalWrapper(
            entityType="dataset",
            entityUrn=urn,
            aspect=GlobalTagsClass(tags=tag_associations),
        )
        graph.emit(mcp_tags)

        record["datahub_written"] = True
        record["mode"] = "datahub_graph_emitter"
        INVESTIGATION_HISTORY.append(record)

        return {
            "success": True,
            "datahub_written": True,
            "mode": "datahub_graph_emitter",
            "details": payload,
        }
    except Exception as ex:
        logger.debug(f"DataHub Graph SDK emitter failed: {ex}")

    # Method 2: REST aspect ingest proposal via httpx
    try:
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
            record["datahub_written"] = True
            record["mode"] = "gms_rest"
            INVESTIGATION_HISTORY.append(record)
            return {
                "success": True,
                "datahub_written": True,
                "mode": "gms_rest",
                "details": payload,
            }
    except Exception as e:
        logger.warning(f"Could not reach DataHub GMS for live write-back: {e}")

    record["datahub_written"] = False
    record["mode"] = "offline_local_record"
    INVESTIGATION_HISTORY.append(record)

    return {
        "success": False,
        "datahub_written": False,
        "mode": "offline_local_record",
        "error": f"DataHub GMS at {gms_url} unreachable",
        "details": payload,
    }

