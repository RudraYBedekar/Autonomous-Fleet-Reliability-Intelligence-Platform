import importlib

mcp_mod = importlib.import_module("datahub.emitter.mcp")
graph_mod = importlib.import_module("datahub.ingestion.graph.client")
config_mod = importlib.import_module("datahub.ingestion.graph.config")
schema_mod = importlib.import_module("datahub.metadata.schema_classes")

MetadataChangeProposalWrapper = getattr(mcp_mod, "MetadataChangeProposalWrapper")
DataHubGraph = getattr(graph_mod, "DataHubGraph")
DatahubClientConfig = getattr(config_mod, "DatahubClientConfig")
SchemaMetadataClass = getattr(schema_mod, "SchemaMetadataClass")
SchemaFieldClass = getattr(schema_mod, "SchemaFieldClass")
SchemaFieldDataTypeClass = getattr(schema_mod, "SchemaFieldDataTypeClass")
NumberTypeClass = getattr(schema_mod, "NumberTypeClass")
OtherSchemaClass = getattr(schema_mod, "OtherSchemaClass")

graph = DataHubGraph(DatahubClientConfig(server="http://localhost:8080"))

urn = "urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)"

other_schema = OtherSchemaClass(rawSchema="")
fields = [
    SchemaFieldClass(fieldPath="battery_pct", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="HV traction battery state-of-charge %"),
    SchemaFieldClass(fieldPath="battery_temperature", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="Battery pack temperature in Celsius (°C)"),
    SchemaFieldClass(fieldPath="vibration_hz", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="LiDAR mount vibration frequency (Hz)"),
    SchemaFieldClass(fieldPath="health_score", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="Composite vehicle health index (0-100%)"),
    SchemaFieldClass(fieldPath="maintenance_rul_pct", nativeDataType="NUMBER", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="Predicted Remaining Useful Life (%)"),
]

schema_mcp = MetadataChangeProposalWrapper(
    entityType="dataset",
    entityUrn=urn,
    aspect=SchemaMetadataClass(
        schemaName="VehicleHealthFeatures",
        platform="urn:li:dataPlatform:kafka",
        version=0,
        hash="",
        platformSchema=other_schema,
        fields=fields,
    ),
)

try:
    graph.emit(schema_mcp)
    print("SUCCESSFULLY EMITTED SCHEMA METADATA VIA SDK GRAPH CLIENT!")
except Exception as e:
    print("SDK EMIT ERROR:", e)
