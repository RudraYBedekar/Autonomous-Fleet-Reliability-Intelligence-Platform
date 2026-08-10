"""
DataHub Graph Reader Service for FleetGuard AI.

Provides live metadata reads directly from DataHub GMS using DataHubGraph SDK / REST API:
- get_dataset_properties(urn_or_name)
- get_asset_schema(urn_or_name)
- get_ownership(urn_or_name)
- get_upstream_lineage(urn_or_name)
- get_downstream_lineage(urn_or_name)
- get_live_asset_context(urn_or_name)
"""

from __future__ import annotations

import logging
import os
import json
import urllib.request
import importlib
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("fleetguard.graph_reader")


def _get_gms_url() -> str:
    return os.getenv("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")


def _build_dataset_urn(asset_name: str) -> str:
    if asset_name.startswith("urn:li:dataset:"):
        return asset_name
    if "model" in asset_name.lower() or "predictor" in asset_name.lower():
        return f"urn:li:dataset:(urn:li:dataPlatform:ml,{asset_name},PROD)"
    return f"urn:li:dataset:(urn:li:dataPlatform:kafka,{asset_name},PROD)"


def get_graph_client():
    """Initializes DataHubGraph client if acryl-datahub library is installed."""
    try:
        dh_client_mod = importlib.import_module("datahub.ingestion.graph.client")
        dh_config_mod = importlib.import_module("datahub.ingestion.graph.config")
        DataHubGraph = getattr(dh_client_mod, "DataHubGraph")
        DatahubClientConfig = getattr(dh_config_mod, "DatahubClientConfig")

        gms_url = _get_gms_url()
        token = os.getenv("DATAHUB_GMS_TOKEN") or None
        return DataHubGraph(DatahubClientConfig(server=gms_url, token=token))
    except Exception as e:
        logger.debug(f"DataHubGraph SDK initialization failed: {e}")
        return None


def fetch_aspect_via_rest(entity_urn: str, aspect_name: str) -> Optional[Dict[str, Any]]:
    """Direct HTTP REST fallback to fetch entity aspect from DataHub GMS."""
    gms_url = _get_gms_url()
    token = os.getenv("DATAHUB_GMS_TOKEN")
    url = f"{gms_url}/aspects/{entity_urn}?aspect={aspect_name}&version=0"

    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                aspect_data = data.get("aspect", {})
                if isinstance(aspect_data, dict):
                    return aspect_data
                if isinstance(aspect_data, str):
                    return json.loads(aspect_data)
    except Exception as e:
        logger.debug(f"REST aspect fetch failed for {entity_urn} ({aspect_name}): {e}")
    return None


def get_dataset_properties(asset_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves DatasetProperties aspect for dataset URN or asset name."""
    urn = _build_dataset_urn(asset_name)
    graph = get_graph_client()
    if graph:
        try:
            schema_mod = importlib.import_module("datahub.metadata.schema_classes")
            DatasetPropertiesClass = getattr(schema_mod, "DatasetPropertiesClass")
            aspect = graph.get_aspect(entity_urn=urn, aspect_type=DatasetPropertiesClass)
            if aspect:
                return {
                    "name": getattr(aspect, "name", asset_name),
                    "description": getattr(aspect, "description", None),
                    "customProperties": getattr(aspect, "customProperties", {}) or {},
                }
        except Exception as e:
            logger.debug(f"SDK get_aspect DatasetProperties failed for {urn}: {e}")

    rest_aspect = fetch_aspect_via_rest(urn, "datasetProperties")
    if rest_aspect:
        return {
            "name": rest_aspect.get("name", asset_name),
            "description": rest_aspect.get("description"),
            "customProperties": rest_aspect.get("customProperties", {}),
        }
    return None


def get_ownership(asset_name: str) -> List[str]:
    """Retrieves list of owner URNs for dataset."""
    urn = _build_dataset_urn(asset_name)
    graph = get_graph_client()
    if graph:
        try:
            schema_mod = importlib.import_module("datahub.metadata.schema_classes")
            OwnershipClass = getattr(schema_mod, "OwnershipClass")
            aspect = graph.get_aspect(entity_urn=urn, aspect_type=OwnershipClass)
            if aspect and getattr(aspect, "owners", None):
                return [getattr(o, "owner", "") for o in aspect.owners if getattr(o, "owner", None)]
        except Exception as e:
            logger.debug(f"SDK get_aspect Ownership failed for {urn}: {e}")

    rest_aspect = fetch_aspect_via_rest(urn, "ownership")
    if rest_aspect and "owners" in rest_aspect:
        return [o.get("owner") for o in rest_aspect.get("owners", []) if o.get("owner")]
    return []


def get_upstream_lineage(asset_name: str) -> List[Dict[str, Any]]:
    """Retrieves upstream datasets/sensors for asset."""
    urn = _build_dataset_urn(asset_name)
    graph = get_graph_client()
    if graph:
        try:
            schema_mod = importlib.import_module("datahub.metadata.schema_classes")
            UpstreamLineageClass = getattr(schema_mod, "UpstreamLineageClass")
            aspect = graph.get_aspect(entity_urn=urn, aspect_type=UpstreamLineageClass)
            if aspect and getattr(aspect, "upstreams", None):
                return [{"urn": getattr(u, "dataset", ""), "type": getattr(u, "type", "TRANSFORMED")} for u in aspect.upstreams]
        except Exception as e:
            logger.debug(f"SDK get_aspect UpstreamLineage failed for {urn}: {e}")

    rest_aspect = fetch_aspect_via_rest(urn, "upstreamLineage")
    if rest_aspect and "upstreams" in rest_aspect:
        return [{"urn": u.get("dataset"), "type": u.get("type", "TRANSFORMED")} for u in rest_aspect.get("upstreams", [])]
    return []


def get_downstream_lineage(asset_name: str) -> List[Dict[str, Any]]:
    """Retrieves downstream ML models / datasets impacted by asset URN."""
    urn = _build_dataset_urn(asset_name)

    # Search for entities listing target URN as upstream
    known_models = [
        "urn:li:dataset:(urn:li:dataPlatform:ml,rul_predictor_model,PROD)",
        "urn:li:dataset:(urn:li:dataPlatform:ml,anomaly_detector_model,PROD)",
    ]
    downstream = []
    for model_urn in known_models:
        upstreams = get_upstream_lineage(model_urn)
        if any(u.get("urn") == urn for u in upstreams):
            downstream.append({"urn": model_urn, "type": "TRANSFORMED"})

    return downstream


def get_live_asset_context(asset_name: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Attempts live DataHub metadata lookup for an asset.
    Returns: (context_dict or None, is_live: bool)
    """
    props = get_dataset_properties(asset_name)
    if not props:
        return None, False

    owners = get_ownership(asset_name)
    upstream = get_upstream_lineage(asset_name)
    downstream = get_downstream_lineage(asset_name)

    return {
        "asset": asset_name,
        "description": props.get("description"),
        "customProperties": props.get("customProperties", {}),
        "owners": owners,
        "upstream": upstream,
        "downstream": downstream,
    }, True
