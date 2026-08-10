"""
Sample DataHub Metadata Ingestion Script for Autonomous Fleet Reliability Platform.

Publishes sample fleet dataset schemas, ML Model entities, and complete lineage graph into DataHub Core:
- vehicle_health_features (Dataset)
- fleet_trip_manifests (Dataset)
- car-001_lidar_sensor (Upstream Hardware Sensor)
- rul_predictor (Downstream ML Model)
- anomaly_detector (Downstream ML Model)

Usage:
    python -m backend.datahub.ingest_sample
"""

from __future__ import annotations

import os
import importlib


def ingest_fleet_metadata() -> None:
    """Publishes fleet metadata entities, ML models, and lineage graph directly to DataHub GMS."""
    gms_url = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")
    print(f"Ingesting fleet metadata & ML lineage into DataHub GMS at: {gms_url}")

    try:
        mcp_mod = importlib.import_module("datahub.emitter.mcp")
        graph_mod = importlib.import_module("datahub.ingestion.graph.client")
        config_mod = importlib.import_module("datahub.ingestion.graph.config")
        schema_mod = importlib.import_module("datahub.metadata.schema_classes")

        MetadataChangeProposalWrapper = getattr(mcp_mod, "MetadataChangeProposalWrapper")
        DataHubGraph = getattr(graph_mod, "DataHubGraph")
        DatahubClientConfig = getattr(config_mod, "DatahubClientConfig")
        AuditStampClass = getattr(schema_mod, "AuditStampClass")
        DatasetPropertiesClass = getattr(schema_mod, "DatasetPropertiesClass")
        OwnerClass = getattr(schema_mod, "OwnerClass")
        OwnershipClass = getattr(schema_mod, "OwnershipClass")
        OwnershipTypeClass = getattr(schema_mod, "OwnershipTypeClass")
        UpstreamClass = getattr(schema_mod, "UpstreamClass")
        UpstreamLineageClass = getattr(schema_mod, "UpstreamLineageClass")
        SchemaMetadataClass = getattr(schema_mod, "SchemaMetadataClass")
        SchemaFieldClass = getattr(schema_mod, "SchemaFieldClass")
        SchemaFieldDataTypeClass = getattr(schema_mod, "SchemaFieldDataTypeClass")
        NumberTypeClass = getattr(schema_mod, "NumberTypeClass")

        graph = DataHubGraph(DatahubClientConfig(server=gms_url))
    except Exception as err:
        print(f"Warning: DataHub Graph SDK connection failed: {err}")
        return

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
                "owner": "fleet_ops",
            },
        ),
    )
    graph.emit(ds1_mcp)

    # SchemaMetadata aspect
    try:
        OtherSchemaClass = getattr(schema_mod, "OtherSchemaClass")
        schema_mcp = MetadataChangeProposalWrapper(
            entityType="dataset",
            entityUrn="urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
            aspect=SchemaMetadataClass(
                schemaName="VehicleHealthFeatures",
                platform="urn:li:dataPlatform:kafka",
                version=0,
                hash="",
                platformSchema=OtherSchemaClass(rawSchema=""),
                fields=[
                    SchemaFieldClass(fieldPath="battery_pct", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="HV battery state of charge %"),
                    SchemaFieldClass(fieldPath="battery_temperature", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="Battery pack temperature in Celsius"),
                    SchemaFieldClass(fieldPath="vibration_hz", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="LiDAR mount vibration frequency"),
                    SchemaFieldClass(fieldPath="health_score", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="Composite vehicle health index"),
                    SchemaFieldClass(fieldPath="maintenance_rul_pct", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="Predicted Remaining Useful Life %"),
                ],
            ),
        )
        graph.emit(schema_mcp)
    except Exception as se:
        print(f"SchemaMetadata emission note: {se}")

    # Ownership aspect
    owner_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
        aspect=OwnershipClass(
            owners=[
                OwnerClass(
                    owner="urn:li:corpuser:fleet_ops",
                    type=OwnershipTypeClass.TECHNICAL_OWNER,
                )
            ]
        ),
    )
    graph.emit(owner_mcp)

    # 2. Downstream ML Model 1: RUL Predictor
    ml1_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:ml,rul_predictor_model,PROD)",
        aspect=DatasetPropertiesClass(
            name="rul_predictor_model",
            description="Production XGBoost model predicting battery/component Remaining Useful Life (RUL %).",
            customProperties={
                "model_type": "XGBoostRegressor",
                "accuracy_mae": "1.4%",
                "status": "ACTIVE_PRODUCTION",
            },
        ),
    )
    graph.emit(ml1_mcp)

    # 3. Downstream ML Model 2: Isolation Forest Anomaly Detector
    ml2_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:ml,anomaly_detector_model,PROD)",
        aspect=DatasetPropertiesClass(
            name="anomaly_detector_model",
            description="Production Isolation Forest model flagging telemetry anomalies & hardware sensor drift.",
            customProperties={
                "model_type": "IsolationForest",
                "contamination": "0.05",
                "status": "ACTIVE_PRODUCTION",
            },
        ),
    )
    graph.emit(ml2_mcp)

    # 4. Upstream Hardware Sensor: car-001_lidar_sensor
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

    # 5. Upstream Lineage: car-001_lidar_sensor -> vehicle_health_features
    lineage_up_mcp = MetadataChangeProposalWrapper(
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
    graph.emit(lineage_up_mcp)

    # 6. Downstream Lineage: vehicle_health_features -> ML Models
    lineage_down1_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:ml,rul_predictor_model,PROD)",
        aspect=UpstreamLineageClass(
            upstreams=[
                UpstreamClass(
                    dataset="urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
                    type="TRANSFORMED",
                    auditStamp=AuditStampClass(time=1000, actor="urn:li:corpuser:fleet_ops"),
                )
            ]
        ),
    )
    graph.emit(lineage_down1_mcp)

    lineage_down2_mcp = MetadataChangeProposalWrapper(
        entityType="dataset",
        entityUrn="urn:li:dataset:(urn:li:dataPlatform:ml,anomaly_detector_model,PROD)",
        aspect=UpstreamLineageClass(
            upstreams=[
                UpstreamClass(
                    dataset="urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
                    type="TRANSFORMED",
                    auditStamp=AuditStampClass(time=1000, actor="urn:li:corpuser:fleet_ops"),
                )
            ]
        ),
    )
    graph.emit(lineage_down2_mcp)

    print("SUCCESS: Emitted fleet datasets, ML models, and complete lineage graph into DataHub Core!")
    print("Refresh http://localhost:9002 in your browser to inspect the entities and lineage!")


if __name__ == "__main__":
    ingest_fleet_metadata()
