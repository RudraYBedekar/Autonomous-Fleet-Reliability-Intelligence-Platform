"""
Sample DataHub Metadata Ingestion Script for Autonomous Fleet Reliability Platform.

Publishes sample fleet dataset schemas and lineage entities into DataHub Core:
- vehicle_health_features (Dataset)
- fleet_trip_manifests (Dataset)
- car-001_lidar_sensor (Upstream Hardware Sensor)

Usage:
    python -m backend.datahub.ingest_sample
"""

from __future__ import annotations

import os
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.metadata.schema_classes import (
    AuditStampClass,
    DatasetPropertiesClass,
    UpstreamClass,
    UpstreamLineageClass,
)


def ingest_fleet_metadata() -> None:
    """Publishes fleet metadata entities and lineage directly to DataHub GMS."""
    gms_url = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")
    print(f"Ingesting fleet metadata into DataHub GMS at: {gms_url}")

    graph = DataHubGraph(DatahubClientConfig(server=gms_url))

    # 1. vehicle_health_features dataset
    ds1_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
        aspect=DatasetPropertiesClass(
            name="vehicle_health_features",
            description="Real-time electric vehicle telemetry features including LiDAR vibration frequency, battery thermal temperature, motor RPM, and remaining useful life (RUL %).",
            customProperties={
                "fleet_size": "15",
                "update_frequency": "1000ms",
                "domain": "fleet_reliability",
            },
        ),
    )
    graph.emit(ds1_mcp)

    # 2. fleet_trip_manifests dataset
    ds2_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:postgres,fleet_trip_manifests,PROD)",
        aspect=DatasetPropertiesClass(
            name="fleet_trip_manifests",
            description="Passenger manifests, pickup/destination coordinates, and driver contacts for Redwood City autonomous EV fleet.",
            customProperties={
                "city": "Redwood City, CA",
                "status": "Active",
            },
        ),
    )
    graph.emit(ds2_mcp)

    # 3. car-001_lidar_sensor upstream hardware sensor
    ds3_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:kafka,car-001_lidar_sensor,PROD)",
        aspect=DatasetPropertiesClass(
            name="car-001_lidar_sensor",
            description="Raw LiDAR frequency sensor feed for autonomous vehicle car-001.",
            customProperties={"hardware_vendor": "Velodyne", "bus": "CAN_BUS_0"},
        ),
    )
    graph.emit(ds3_mcp)

    # 4. Lineage: car-001_lidar_sensor -> vehicle_health_features
    lineage_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
        aspect=UpstreamLineageClass(
            upstreams=[
                UpstreamClass(
                    dataset="urn:li:dataset:(urn:li:dataPlatform:kafka,car-001_lidar_sensor,PROD)",
                    type="TRANSFORMED",
                    auditStamp=AuditStampClass(
                        time=1000,
                        actor="urn:li:corpuser:fleet_dispatcher",
                    ),
                )
            ]
        ),
    )
    graph.emit(lineage_mcp)

    print("SUCCESS: Emitted fleet datasets and lineage graph into DataHub Core!")
    print("Refresh http://localhost:9002 in your browser to inspect the dataset entities!")


if __name__ == "__main__":
    ingest_fleet_metadata()
