# Autonomous Fleet Reliability Intelligence Platform 🚜⚡

An enterprise-grade, real-time fleet intelligence platform for autonomous electric vehicles (EVs) featuring telemetry streaming, anomaly detection, Remaining Useful Life (RUL) prediction, **AWS Bedrock LLM reasoning**, and official **DataHub MCP Server / Agent Context Kit** metadata integration.

Built for the **Build with DataHub Agent Hackathon**.

---

## 🌟 Key Capabilities & Hackathon Features

- 🤖 **AI Fleet Assistant & Copilot (`CopilotPanel.jsx`)**:
  - Natural language vehicle search for 15 live Redwood City autonomous EVs (`car-001` through `car-015`).
  - Interactive **Passenger & Route Manifest Cards** (*Pickup Address → Destination Address, Driver Contact, Live Speed, Battery %, Health Index %*).
  - **`Focus on Map`**: Instantly tracks & centers the vehicle on the live 3D MapLibre/Deck.gl canvas.
  - **`Run RCA`**: Triggers automated LLM Root Cause Diagnostics.
  - **Clean Executive Plain Text**: Outputs 100% professional operational reports without raw markdown syntax.

- 🔗 **Official DataHub MCP Server Integration (`acryldata/mcp-server-datahub`)**:
  - **Zero PAT Dependency**: 100% pluggable authentication using environment variables (`DATAHUB_GMS_URL`, `DATAHUB_GMS_TOKEN`, `DATAHUB_MCP_ENABLED`).
  - **SSH Reverse Tunnel Architecture**: Seamlessly connects AWS EC2 FastAPI backend to local Windows Docker DataHub Core (`127.0.0.1:18080` → `localhost:8080`).
  - **Distinct Health Statuses**: Reports `datahub_connected` (GMS REST health) and `mcp_connected` (MCP Server subprocess status) independently.
  - **Zero Mock Metadata**: Unconfigured state cleanly returns `datahub_connected: false` without faking metadata.

- 🧠 **AWS Bedrock Reasoning Engine (`backend/services/bedrock_client.py`)**:
  - Leverages AWS Bedrock multi-model client with fallback reasoning for automated Root Cause Analysis (RCA) and maintenance remediation plans.

- 📡 **Real-Time Telemetry & Predictive Analytics**:
  - Isolation Forest anomaly detection for LiDAR vibration frequency (Hz), battery thermal temp (°C), and motor RPM.
  - Remaining Useful Life (RUL) forecasting.

---

## 🏗️ Architecture Diagram

```
┌────────────────────────────────────────────────────────┐
│              AWS EC2 FastAPI Backend (Port 8000)       │
│                                                        │
│   backend/routers/datahub.py & backend/datahub/         │
│     ├── GET /api/datahub/status                        │
│     ├── GET /api/datahub/asset/{asset_name}            │
│     └── GET /api/datahub/fleetguard-context/{asset}    │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            │ (stdio transport)              │ (Context payload)
            ▼                                ▼
┌────────────────────────┐      ┌────────────────────────┐
│  Official DataHub MCP  │      │      AWS Bedrock       │
│  Server (via uvx/pip)  │      │     Reasoning LLM      │
└───────────┬────────────┘      └────────────────────────┘
            │ (GMS REST API)
            ▼
┌────────────────────────────────────────────────────────┐
│    SSH Reverse Tunnel (EC2 127.0.0.1:18080)            │
│    Forwarded to Windows localhost:8080 (DataHub Core)  │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Frontend**: React, Vite, Vanilla CSS (Glassmorphism), Deck.gl, MapLibre GL
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, WebSockets, Python 3.12
- **Metadata Context**: Official `mcp-server-datahub` (`acryldata/mcp-server-datahub`), `acryl-datahub`
- **AI & Reasoning**: AWS Bedrock, LangChain, Scikit-learn (Isolation Forest)
- **Streaming & Infrastructure**: Apache Kafka (KRaft Mode), Nginx, AWS EC2

---

## 🌐 API Access Points

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /api/datahub/status` | `GET` | Health check for DataHub GMS & MCP Server connection |
| `GET /api/datahub/asset/{asset_name}` | `GET` | Normalized DataHub asset schema, lineage, and ownership |
| `GET /api/datahub/fleetguard-context/{asset_name}` | `GET` | DataHub context payload prepared for AWS Bedrock |
| `POST /api/ai/ask` | `POST` | AI Fleet Assistant query & vehicle search |
| `POST /api/ai/diagnose/{vehicle_id}` | `POST` | Automated LLM Root Cause Analysis (RCA) |
| `GET /api/ai/fleet-brief` | `GET` | Executive fleet health brief |

---

## 🚀 Quick Setup Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/RudraYBedekar/Autonomous-Fleet-Reliability-Intelligence-Platform.git
cd Autonomous-Fleet-Reliability-Intelligence-Platform

# Install Python requirements
pip install -r requirements.txt
pip install mcp-server-datahub
```

### 2. Configure Environment Variables (`.env`)
```env
DATAHUB_GMS_URL=http://127.0.0.1:18080
DATAHUB_GMS_TOKEN=
DATAHUB_MCP_ENABLED=true
```

### 3. Establish SSH Reverse Tunnel (For EC2 Deployment)
From your **Windows PowerShell**:
```powershell
ssh -i "path\to\your-key.pem" -R 18080:localhost:8080 ubuntu@<EC2_PUBLIC_IP>
```

### 4. Verify Connection
Run backend diagnostic script:
```bash
python -m backend.datahub.check_connection
```

### 5. Ingest Sample Fleet Metadata into DataHub
```bash
python -m backend.datahub.ingest_sample
```
Open **[http://localhost:9002](http://localhost:9002)** to inspect dataset schemas and lineage graphs in the DataHub UI!

---

## 📄 Documentation
- 📘 **[docs/DATAHUB_MCP_SETUP.md](docs/DATAHUB_MCP_SETUP.md)**: Detailed DataHub MCP Server architecture, SSH tunnel setup, and Bedrock integration design.
- 📋 **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**: Complete progress summary of all features built till now.
