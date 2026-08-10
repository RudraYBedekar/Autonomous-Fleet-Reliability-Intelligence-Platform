import json
import urllib.request
import urllib.error

gms_url = "http://localhost:8080"

schema_dict = {
  "schemaName": "VehicleHealthFeatures",
  "platform": "urn:li:dataPlatform:kafka",
  "version": 0,
  "created": {
    "time": 0,
    "actor": "urn:li:corpuser:unknown"
  },
  "lastModified": {
    "time": 0,
    "actor": "urn:li:corpuser:unknown"
  },
  "hash": "",
  "platformSchema": {
    "otherSchema": {
      "rawSchema": ""
    }
  },
  "fields": [
    {
      "fieldPath": "battery_pct",
      "nullable": False,
      "description": "HV battery state of charge %",
      "type": {"type": {"numberType": {}}},
      "nativeDataType": "number"
    },
    {
      "fieldPath": "battery_temperature",
      "nullable": False,
      "description": "Battery pack temperature in Celsius (°C)",
      "type": {"type": {"numberType": {}}},
      "nativeDataType": "number"
    },
    {
      "fieldPath": "vibration_hz",
      "nullable": False,
      "description": "LiDAR mount vibration frequency (Hz)",
      "type": {"type": {"numberType": {}}},
      "nativeDataType": "number"
    },
    {
      "fieldPath": "health_score",
      "nullable": False,
      "description": "Composite vehicle health index (0-100%)",
      "type": {"type": {"numberType": {}}},
      "nativeDataType": "number"
    },
    {
      "fieldPath": "maintenance_rul_pct",
      "nullable": False,
      "description": "Predicted Remaining Useful Life (%)",
      "type": {"type": {"numberType": {}}},
      "nativeDataType": "number"
    }
  ]
}

payload = {
    "proposal": {
        "entityType": "dataset",
        "entityUrn": "urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)",
        "aspectName": "schemaMetadata",
        "changeType": "UPSERT",
        "aspect": {
            "contentType": "application/json",
            "value": json.dumps(schema_dict)
        }
    }
}

data_bytes = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    f"{gms_url}/aspects?action=ingestProposal",
    data=data_bytes,
    headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req) as resp:
        print("SUCCESS! Status code:", resp.status, resp.read().decode("utf-8"))
except urllib.error.HTTPError as err:
    print("FAILED:", err.code, err.read().decode("utf-8", errors="ignore"))
