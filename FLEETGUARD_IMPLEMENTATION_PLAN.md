# FleetGuard AI Implementation Plan — DataHub Agent Hackathon

## Executive Summary
This document presents the technical implementation plan for extending the **Autonomous Fleet Reliability Intelligence Platform** with the **FleetGuard AI Layer** for the **Build with DataHub Agent Hackathon**.

The extension introduces an autonomous investigation agent layer combining:
1. **AWS Bedrock** as the reasoning and root-cause analysis LLM engine.
2. **DataHub** as the enterprise metadata, schema, entity ownership, dataset lineage, and audit context layer.

The existing telemetry processing, 10 Hz simulation generator, Deck.gl visualization, rule-based alerts, ML algorithms, SQLite/SQLAlchemy models, and EC2/Nginx/systemd deployment pipeline will remain **100% intact and non-breaking**.

---

## 1. Current Architecture Analysis

### A. Telemetry & Simulation Flow
- **Generator**: `backend/services/generator.py` runs an async loop producing 10 Hz telemetry for 15 electric vehicles (`car-001` to `car-015`) in Redwood City, CA.
- **WebSocket Hub**: `backend/routers/websockets.py` broadcasts validated Pydantic `VehicleTelemetry` models to connected clients.
- **In-Memory Store**: `backend/services/telemetry_store.py` buffers recent sliding window telemetry (5 min history).
- **Kafka Option**: Optional bridge in `streaming/producer.py` & `streaming/consumer.py` + `backend/routers/websockets.py`.

### B. Anomaly & Alert Engine
- **Rule-Based Alerts**: `backend/services/alerts.py` evaluates metrics (`battery_pct < 15%`, `health_score < 70%`, `maintenance_rul_pct < 20%`, `road_zone` speeding, `stalled_mid_route`) and pushes alerts into `_active` list.
- **ML Anomaly Detection**: `ml/anomaly_detector.py` (Z-Score & heuristic RUL) and `analytics_engine.py` (Isolation Forest across `temperature_c`, `voltage_v`, `vibration_g`).
- **Expert RCA**: `ml/rca_engine.py` (`RootCauseAnalyzer`) maps sensor types (`LiDAR`, `Battery`, `EngineRPM`) to heuristic diagnoses.

### C. Database & Schemas
- **SQLite Database**: `telemetry.db` / `backend/database/db.py` managed via SQLAlchemy.
- **Model**: `TelemetryRecord` in `backend/database/models.py` (`id`, `timestamp`, `vehicle_id`, `sensor_id`, `temperature_c`, `voltage_v`, `vibration_g`, `status`, `ml_anomaly`, `predicted_rul_hours`).
- **Schemas**: `backend/schemas/telemetry.py` (`VehicleTelemetry`), `backend/schemas/dispatch.py`.

### D. FastAPI Router Layer
- `backend/main.py`: Entry point including routers `telemetry`, `websockets`, `ai`, and `fleet`.
- `backend/routers/ai.py`: Currently contains a stub `/api/ai/ask` endpoint returning mock data.

### E. Frontend Application
- Built with React 19, Vite 8, Tailwind CSS, Deck.gl, MapLibre GL.
- Root container `frontend/src/App.jsx` handles WebSocket telemetry state and renders `FleetPanel` & `FleetMap`.
- `frontend/src/components/CopilotPanel.jsx`: Currently an empty 0-byte file ready for UI implementation.

---

## 2. Files to be Reused (Unmodified Core)

| File Path | Role in FleetGuard Flow |
| :--- | :--- |
| `backend/main.py` | FastAPI app setup — mount new router/services without changing existing startup behavior. |
| `backend/database/models.py` | Source of historical telemetry records and persisted anomaly flags. |
| `backend/services/alerts.py` | Primary trigger source for live rule-based critical alerts. |
| `backend/services/telemetry_store.py` | Quick retrieval of recent 5-minute telemetry windows for vehicle context. |
| `ml/rca_engine.py` | Local domain knowledge seed fed into Bedrock context prompt. |
| `analytics_engine.py` | Isolation Forest statistical baseline data. |
| `frontend/src/App.jsx` | Integration host for the `CopilotPanel` / FleetGuard UI component. |
| `deploy/nginx-fleet.conf` & `fleet-api.service` | Reverse proxy routing (`/api/`) and systemd supervisor on EC2. |

---

## 3. New Files Required

```
Telemetry Project/
├── backend/
│   ├── services/
│   │   ├── datahub_client.py       # DataHub REST / Python SDK integration (metadata, lineage, tags)
│   │   ├── bedrock_client.py       # AWS Bedrock client for LLM reasoning & investigation
│   │   └── fleetguard_agent.py     # Main agent orchestrator connecting Detection -> DataHub -> Bedrock -> DataHub
│   └── routers/
│       └── fleetguard.py           # Dedicated FleetGuard API endpoints
├── frontend/
│   └── src/
│       └── components/
│           ├── CopilotPanel.jsx    # Complete AI investigation drawer & natural language chat interface
│           └── FleetGuardModal.jsx # Detailed Incident Investigation breakdown modal
└── FLEETGUARD_IMPLEMENTATION_PLAN.md # This document
```

---

## 4. Architectural & Data Flow Specification

### The FleetGuard Investigation Loop

```
┌─────────────────────────┐
│ 1. Telemetry Alert      │  (Critical Battery, Health Score < 70%, LiDAR Vibration, Isolation Forest Anomaly)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. FleetGuard Trigger   │  (Triggered automatically on Critical Alert OR on manual user click)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. DataHub Metadata     │  Queries DataHub for:
│    Lookup Client        │  - Vehicle & Sensor dataset schemas (`urn:li:dataset:...`)
│                         │  - Component owner / Maintenance team (`urn:li:corpuser:...`)
│                         │  - Upstream hardware supplier & downstream fleet route dependencies
│                         │  - Historical assertions, tags, and operational metadata
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. AWS Bedrock          │  Sends aggregated context payload:
│    Reasoning Engine     │  - Live Telemetry Snapshot & 5-min trend
│                         │  - Expert RCA heuristic baseline
│                         │  - DataHub Metadata, Ownership, Lineage, and Governance tags
│                         │  Prompts Claude 3.5 Sonnet / Haiku via AWS Bedrock runtime
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 5. Structured Remedy &  │  Receives structured JSON: Root Cause, Operational Impact, Remediation Steps,
│    DataHub Persistence  │  Risk Severity, and Actionable Fleet Commands.
│                         │  Emits metadata tags (`fleetguard_investigated`, `root_cause:*`) and audit event to DataHub.
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 6. Frontend Display     │  Rendered interactively in `CopilotPanel.jsx` / `FleetGuardModal.jsx`
└───────────┬─────────────┘
```

---

## 5. Integration Details

### A. AWS Bedrock Integration (`backend/services/bedrock_client.py`)
- **SDK**: `boto3` (`bedrock-runtime` client).
- **Default Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (or `amazon.titan-text-express-v1` fallback).
- **Authentication**: AWS IAM Credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`).
- **Functionality**:
  - `investigate_incident(incident_data, datahub_context)`: Formats a structured system prompt requiring strictly typed JSON response containing:
    - `root_cause_analysis`: Concise explanation of failure mechanism.
    - `impact_assessment`: Passenger safety, route delay, hardware risk.
    - `remediation_plan`: Immediate dispatch/maintenance actions.
    - `confidence_score`: 0–100%.
    - `recommended_action_type`: `reroute`, `dispatch_service`, `passenger_notify`, `isolate_vehicle`.
  - Fallback logic for offline/demo mode when AWS credentials are not set.

### B. DataHub Metadata Layer (`backend/services/datahub_client.py`)
- **SDK**: `acryl-datahub` Python SDK or direct DataHub GMS REST API (`http://<DATAHUB_HOST>:8080`).
- **Entity URNs**:
  - Fleet Datasets: `urn:li:dataset:(urn:li:dataPlatform:kafka,telemetry.live,PROD)`
  - Vehicle Entities: `urn:li:dataset:(urn:li:dataPlatform:fleet,car-001,PROD)`
  - Sensor Schema: `urn:li:dataset:(urn:li:dataPlatform:sensors,lidar-telemetry,PROD)`
  - Owners: `urn:li:corpuser:fleet_ops_team`, `urn:li:corpuser:hardware_eng`
- **Capabilities**:
  - `get_dataset_metadata(dataset_urn)`: Fetch schema, description, ownership, tags.
  - `get_entity_lineage(dataset_urn)`: Fetch upstream sensor pipeline & downstream dispatch services.
  - `emit_investigation_result(vehicle_id, incident_id, investigation_result)`: Add DataHub tags (e.g. `Tag: FleetGuard-Investigated`, `Tag: Severity-Critical`), post structured operational documentation aspect, or record custom assertion pass/fail status.

---

## 6. API Endpoint Contracts

New API Router: `backend/routers/fleetguard.py` (mounted at `/api/fleetguard`)

### 1. `POST /api/fleetguard/investigate`
- **Request Body**:
  ```json
  {
    "vehicle_id": "car-003",
    "alert_code": "battery_critical",
    "alert_message": "car-003 battery critical (14%) — auto-routing to charger",
    "severity": "critical"
  }
  ```
- **Response**:
  ```json
  {
    "incident_id": "fg-inc-20260809-003",
    "vehicle_id": "car-003",
    "timestamp": "2026-08-09T19:30:00Z",
    "telemetry_summary": {
      "battery_pct": 14.0,
      "health_score": 68.5,
      "speed_kmh": 22.4,
      "road_zone": "arterial"
    },
    "datahub_context": {
      "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:fleet,car-003,PROD)",
      "owner": "fleet_ops_team",
      "upstream_lineage": ["sensor.battery_management_system"],
      "governance_tags": ["Production", "EV-Battery-Pack-V2"]
    },
    "ai_analysis": {
      "root_cause_analysis": "Rapid cell voltage imbalance detected under high acceleration thermal load.",
      "impact_assessment": "High risk of mid-route immobilization if fast charge is delayed.",
      "remediation_plan": "1. Maintain priority route to Station B. 2. Limit maximum speed to 30 km/h.",
      "confidence_score": 92,
      "recommended_action_type": "reroute"
    },
    "datahub_persisted": true
  }
  ```

### 2. `GET /api/fleetguard/investigations/{vehicle_id}`
- Returns history of past FleetGuard AI investigations for the specified vehicle.

### 3. `GET /api/fleetguard/lineage/{vehicle_id}`
- Returns graph format of DataHub lineage & metadata relationships for visualization.

---

## 7. Frontend Integration (`CopilotPanel.jsx`)

Update `CopilotPanel.jsx` to render:
1. **Live Incident Feed**: Displays incoming alerts with an **"Investigate with FleetGuard"** button.
2. **Investigation Result Card**:
   - **DataHub Badges**: Owner, DataHub Schema URN, Lineage tags.
   - **Bedrock Insights**: Root Cause, Operational Impact, Action Plan with Confidence Gauge.
   - **Action Trigger**: One-click dispatch actions (`Call Vehicle`, `Notify Passengers`, `Reroute`).
3. **Interactive AI Chat Assistant**: Ask freeform context-aware questions against fleet state, Bedrock, and DataHub metadata.

---

## 8. Environment Variables Specification

Add the following to `.env.example` and `.env`:

```env
# FleetGuard AI Layer Configuration

# AWS Bedrock Settings
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# DataHub Integration
DATAHUB_GMS_URL=http://localhost:8080
DATAHUB_TOKEN=your_datahub_pat_token_optional
DATAHUB_DEFAULT_ENV=PROD

# Feature Toggle
ENABLE_FLEETGUARD_AI=true
```

---

## 9. Safest Implementation Order

1. **Step 1: Environment & Requirements Setup**
   - Add `boto3` and `acryl-datahub` to `requirements.txt`.
   - Update `.env.example` with Bedrock and DataHub configuration keys.

2. **Step 2: Backend DataHub & Bedrock Service Modules**
   - Implement `backend/services/datahub_client.py` with fallback mock metadata for local testing when GMS is offline.
   - Implement `backend/services/bedrock_client.py` with mock response fallback when AWS credentials are not set.

3. **Step 3: Agent Orchestrator & API Router**
   - Implement `backend/services/fleetguard_agent.py` to coordinate Telemetry + DataHub + Bedrock + Persistence.
   - Implement `backend/routers/fleetguard.py` and register it in `backend/main.py`.

4. **Step 4: Frontend Copilot Component**
   - Populate `frontend/src/components/CopilotPanel.jsx` with dark-mode, high-aesthetic layout.
   - Mount `CopilotPanel` in `frontend/src/App.jsx` or as a toggle drawer in `FleetPanel.jsx`.

5. **Step 5: Automated & Manual Verification**
   - Run backend FastAPI tests with `httpx` / `pytest`.
   - Verify `/api/fleetguard/investigate` response.
   - Test UI interaction on EC2 / local Vite dev server.
