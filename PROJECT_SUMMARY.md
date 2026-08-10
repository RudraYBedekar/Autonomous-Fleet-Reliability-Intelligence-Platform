# 📜 Project Summary — Autonomous Fleet Reliability Intelligence Platform

## Overview
This document summarizes all major architectural enhancements, AI integrations, DataHub MCP Server connections, and cloud deployment workflows implemented in this project.

---

## 1. 🤖 AI Fleet Assistant & Vehicle Search Console (`CopilotPanel.jsx`)
- **Glassmorphic Chatbot UI**: Floating AI Assistant button with quick suggestion chips (*"Search car-003"*, *"Passenger Summary"*, *"Low Battery EVs"*, *"Active Alerts"*, *"Fleet Brief"*).
- **Interactive Visual Cards**:
  - **Passenger & Route Manifest**: Pickup Address → Destination Address, Driver Contact info & phone dial link.
  - **Telemetry Grid**: Ground Speed (km/h), Battery %, Health Index %, Maintenance RUL %.
  - **`Focus on Map`**: Centers and tracks vehicle on live 3D Deck.gl map.
  - **`Run RCA`**: Triggers automated LLM Root Cause Diagnostics.
- **Executive Plain Text**: Formatted to output 100% clean operational reports (no `**`, `###`, `•`, or emojis).

---

## 2. 🔗 Official DataHub MCP Server Integration (`acryldata/mcp-server-datahub`)
- **Zero PAT Authentication**: Pluggable via environment variables (`DATAHUB_GMS_URL`, `DATAHUB_GMS_TOKEN`, `DATAHUB_MCP_ENABLED`).
- **SSH Reverse Tunnel Architecture**: Connects AWS EC2 FastAPI backend (`http://127.0.0.1:18080`) to Windows Docker DataHub Core (`localhost:8080`).
- **Distinct Statuses**: `datahub_connected` (GMS REST health) and `mcp_connected` (MCP Server subprocess status) reported separately.
- **Zero Fake Data**: Returns explicit `datahub_connected: false` state if unreachable.
- **Sample Ingestion**: Script `python -m backend.datahub.ingest_sample` populates sample dataset entities (`vehicle_health_features`, `fleet_trip_manifests`, `car-001_lidar_sensor`) and lineage into DataHub Core (`http://localhost:9002`).

---

## 3. 🧠 Backend Intelligence & Bedrock Orchestration (`backend/routers/ai.py` & `backend/services/bedrock_client.py`)
- Real-time telemetry snapshot caching in `FleetGenerator`.
- Endpoints:
  - `POST /api/ai/ask`: Vehicle search and operational QA.
  - `POST /api/ai/diagnose/{vehicle_id}`: LLM Root Cause Analysis.
  - `GET /api/ai/fleet-brief`: Executive fleet health summary.
  - `GET /api/datahub/fleetguard-context/{asset_name}`: Prepared DataHub metadata context payload for Bedrock.

---

## 4. 🌐 Environment & Connection Commands

### Windows SSH Reverse Tunnel Command:
```powershell
ssh -i "path\to\your-key.pem" -R 18080:localhost:8080 ubuntu@100.29.80.157
```

### EC2 Backend Connection Test:
```bash
source venv/bin/activate
python -m backend.datahub.check_connection
curl -s http://127.0.0.1:8000/api/datahub/status
```

---

## 5. 🚀 Deployment & GitHub Commits
- **Repository**: `RudraYBedekar/Autonomous-Fleet-Reliability-Intelligence-Platform`
- **Branch**: `main`
- **Latest Commits**:
  - `08251e5`: *refactor(datahub): implement SSH reverse tunnel architecture (127.0.0.1:18080) and distinct GMS vs MCP health status*
  - `a0f6dae`: *feat(datahub): add sample fleet metadata ingestion helper script*
  - `5ad2c2a`: *feat(datahub): populate vehicle_health_features and fleet datasets into DataHub Core UI*
  - `2682a0c`: *fix(deps): upgrade fastapi to >=0.115.0 to resolve Starlette 1.6.0 router compatibility error*
