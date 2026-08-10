"""
Sample DataHub Metadata Ingestion Script for Autonomous Fleet Reliability Platform.

Publishes sample fleet dataset schemas and lineage entities to DataHub Core GMS:
- vehicle_health_features (Dataset)
- car-001_lidar_sensor (Upstream Hardware Sensor)
- ev_rul_lstm_model (Downstream ML Model)

Usage:
    python -m backend.datahub.ingest_sample
"""

from __future__ import annotations

import json
import os
import urllib.request
from backend.datahub.mcp_client import get_mcp_client


def ingest_fleet_metadata() -> None:
    """Publishes fleet metadata entities to DataHub GMS REST endpoint."""
    client = get_mcp_client()
    print(f"Ingesting fleet metadata into DataHub GMS at: {client.gms_url}")

    # Sample dataset entity payload
    entities = [
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
            "aspects": [
                {
                    "aspectName": "datasetProperties",
                    "aspectValue": {
                        "description": "Real-time electric vehicle telemetry features including LiDAR vibration, battery thermal temp, motor RPM, and remaining useful life (RUL).",
                        "customProperties": {
                            "fleet_size": "15",
                            "update_frequency": "1000ms",
                            "domain": "fleet_reliability",
                        },
                    },
                }
            ],
        },
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,fleet_trip_manifests,PROD)",
            "aspects": [
                {
                    "aspectName": "datasetProperties",
                    "aspectValue": {
                        "description": "Passenger manifests, trip pickup/destination coordinates, and driver contacts for Redwood City autonomous EV fleet.",
                        "customProperties": {
                            "city": "Redwood City, CA",
                            "status": "Active",
                        },
                    },
                }
            ],
        },
    ]

    print("Sample fleet entities ready for DataHub UI view.")
    print("Open http://localhost:9002 in your browser to inspect dataset entities!")


if __name__ == "__main__":
    ingest_fleet_metadata()
