import json
import importlib

schema_mod = importlib.import_module("datahub.metadata.schema_classes")
OtherSchemaClass = getattr(schema_mod, "OtherSchemaClass")
o = OtherSchemaClass(rawSchema="")

mcp_mod = importlib.import_module("datahub.emitter.mcp")
SchemaMetadataClass = getattr(schema_mod, "SchemaMetadataClass")
SchemaFieldClass = getattr(schema_mod, "SchemaFieldClass")
SchemaFieldDataTypeClass = getattr(schema_mod, "SchemaFieldDataTypeClass")
NumberTypeClass = getattr(schema_mod, "NumberTypeClass")

sm = SchemaMetadataClass(
    schemaName="VehicleHealthFeatures",
    platform="urn:li:dataPlatform:kafka",
    version=0,
    hash="",
    platformSchema=OtherSchemaClass(rawSchema=""),
    fields=[
        SchemaFieldClass(fieldPath="battery_pct", nativeDataType="number", type=SchemaFieldDataTypeClass(type=NumberTypeClass()), description="HV battery state of charge %")
    ]
)

if hasattr(sm, "to_obj"):
    print("sm.to_obj():", json.dumps(sm.to_obj(), indent=2))
elif hasattr(sm, "dict"):
    print("sm.dict():", json.dumps(sm.dict(), indent=2))
else:
    print("sm dir:", dir(sm))
