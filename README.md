# Autonomous Fleet Reliability Intelligence Platform 🚜⚡

An enterprise-grade, real-time autonomous vehicle fleet intelligence platform for electric vehicles (EVs) featuring simulated 10 Hz telemetry streaming, **Autonomous AI Agent Investigation Loop (`fleetguard_agent.py`)**, **AWS Bedrock LLM reasoning**, Production ML model lineage (`rul_predictor`, `anomaly_detector`), **DataHub Write-Back Persistence**, and official **DataHub MCP Server** metadata integration.

Built for the **Build with DataHub Agent Hackathon**.

**License**: Distributed under the [Apache License 2.0](LICENSE).

---

## 🌟 Key Capabilities & Hackathon Features

- 🤖 **Autonomous AI Agent Loop (`fleetguard_agent.py`)**:
  - **Stage 1 (Alert Ingest)**: Ingests real-time vehicle alerts (battery thermal critical, sensor drift, RUL degradation).
  - **Stage 2 (DataHub MCP Query)**: Fetches schemas, technical owners (`urn:li:corpuser:fleet_ops`), and downstream ML model lineage from DataHub.
  - **Stage 3 (AI Reasoning & Blast Radius)**: Evaluates root cause and downstream ML blast radius (`rul_predictor_model`, `anomaly_detector_model`).
  - **Stage 4 (Safe Mitigation Execution)**: Automatically executes safe rerouting to nearest EV supercharger and notifies dispatcher.
  - **Stage 5 (DataHub Write-Back Persistence)**: Emits investigation tags (`#fleetguard_investigated`, `#auto_mitigated`) and custom properties back into DataHub GMS.

- 🖥️ **Interactive Copilot & Visual Agent Modal (`FleetGuardModal.jsx`)**:
  - **"🤖 Autonomous Agent Loop"**: Instant visual 5-stage agent execution tracker for judges.
  - Natural language vehicle search for 15 live Redwood City autonomous EVs (`car-001` through `car-015`).
  - Interactive **Passenger & Route Manifest Cards** (*Pickup Address → Destination Address, Driver Contact, Live Speed, Battery %, Health Index %*).

- 🔗 **Official DataHub MCP Server & Lineage Integration**:
  - Ingests datasets, ML models (`rul_predictor_model`, `anomaly_detector_model`), ownership, and complete upstream/downstream lineage graphs into DataHub Core.
  - Zero-mock fallback ensures judge demo reproducibility even when offline.

---

## 🏗️ Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Server (Port 8000)                   │
│                                                                        │
│   backend/services/fleetguard_agent.py & backend/routers/fleetguard.py │
│     ├── POST /api/fleetguard/investigate  (5-Stage AI Agent Loop)      │
│     ├── POST /api/datahub/writeback       (GMS Write-Back Persistence) │
│     └── GET  /api/datahub/fleetguard-context/{asset_name}              │
└───────────┬────────────────────────────────┬───────────────────┬───────┘
            │                                │                   │
            │ (stdio transport)              │ (Context payload) │ (Write-Back Aspect)
            ▼                                ▼                   ▼
┌────────────────────────┐      ┌────────────────────────┐  ┌──────────────────┐
│  Official DataHub MCP  │      │      AWS Bedrock       │  │  DataHub Core /  │
│  Server (mcp-server)   │      │     Reasoning LLM      │  │  GMS REST API    │
└───────────┬────────────┘      └────────────────────────┘  └──────────────────┘
            │ (GMS REST)
            ▼
┌────────────────────────────────────────────────────────────────────────┐
│      DataHub Core GMS (Port 8080) & DataHub UI (Port 9002)             │
│      Dataset Schemas • Technical Owners • ML Model Lineage • Write-back│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Frontend**: React, Vite, Vanilla CSS (Glassmorphic Dark UI), Deck.gl, MapLibre GL
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, WebSockets, Python 3.12
- **Metadata Integration**: Official `mcp-server-datahub`, `acryl-datahub` Python SDK
- **AI Agent & Reasoning**: AWS Bedrock, Custom FleetGuard Orchestrator (`fleetguard_agent.py`)
- **Infrastructure**: Docker Compose (`deploy/docker-compose.datahub.yml`), Nginx, AWS EC2

---

## 🌐 API Access Points

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/fleetguard/investigate` | `POST` | Triggers the complete 5-Stage Autonomous AI Agent Loop |
| `POST /api/datahub/writeback` | `POST` | Emits investigation tags (`#fleetguard_investigated`) back to DataHub |
| `GET /api/datahub/status` | `GET` | Health check for DataHub GMS & MCP Server connection |
| `GET /api/datahub/fleetguard-context/{asset_name}` | `GET` | DataHub context payload prepared for AWS Bedrock |
| `POST /api/ai/ask` | `POST` | AI Fleet Assistant query & vehicle search |
| `POST /api/ai/diagnose/{vehicle_id}` | `POST` | Runs FleetGuard agent investigation & diagnostic analysis |

---

## 🚀 Quick Setup Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/RudraYBedekar/Autonomous-Fleet-Reliability-Intelligence-Platform.git
cd Autonomous-Fleet-Reliability-Intelligence-Platform

# Install dependencies (includes boto3 & acryl-datahub)
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```bash
cp .env.example .env
```

### 3. Launch Local DataHub (Optional for Full Live GMS)
```bash
docker-compose -f deploy/docker-compose.datahub.yml up -d
```

### 4. Ingest Fleet Metadata & Downstream ML Model Lineage into DataHub
```bash
python -m backend.datahub.ingest_sample
```
Inspect entities and lineage graphs at **[http://localhost:9002](http://localhost:9002)**.

### 5. Launch Backend & Frontend
```bash
# Terminal 1: Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## 🎬 Recommended 3-Minute Judge Demo Walkthrough

1. **Open Dashboard**: Visit `http://localhost:5173`. View live 15-EV simulated telemetry map and operational alerts.
2. **Open AI Copilot**: Click the Bot icon on top right to open `CopilotPanel.jsx`.
3. **Launch Autonomous Agent Loop**: Click **"🤖 Autonomous Agent Loop"** chip.
4. **Inspect 5-Stage Execution Modal (`FleetGuardModal.jsx`)**:
   - Watch real-time progression from Alert Ingest → DataHub MCP Context Query → Bedrock Blast Radius Reasoning → EV Reroute Dispatch → DataHub GMS Write-Back.
   - Verify impacted ML models (`rul_predictor_model`, `anomaly_detector_model`) and emitted DataHub tags (`#fleetguard_investigated`, `#auto_mitigated`).
5. **Verify DataHub Persistence**: Open `http://localhost:9002` to inspect updated custom properties and tags on `vehicle_health_features`.

---

## 📄 License
This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
