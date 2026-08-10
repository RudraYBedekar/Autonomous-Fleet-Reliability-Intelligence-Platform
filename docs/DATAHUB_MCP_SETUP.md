# DataHub MCP Server Setup & Integration Guide

This guide documents the integration of the **OFFICIAL DataHub MCP Server** (`acryldata/mcp-server-datahub`) with the **Autonomous Fleet Reliability Intelligence Platform** for the **Build with DataHub Agent Hackathon**.

---

## 1. Why We Use DataHub MCP

DataHub MCP (Model Context Protocol) allows LLMs like **AWS Bedrock** and agentic frameworks to dynamically retrieve enterprise metadata—such as dataset schemas, lineage dependencies, component ownership, tags, and operational assertions—without hardcoding database queries or maintaining static documentation.

FastAPI orchestrates the interaction:
`Fleet Telemetry Alert -> DataHub MCP (Context) -> AWS Bedrock (Reasoning) -> Root Cause Report`.

---

## 2. Official GitHub Repository

We strictly use the official Acryl Data MCP Server repository:
👉 **[acryldata/mcp-server-datahub](https://github.com/acryldata/mcp-server-datahub)**

---

## 3. Installation Commands

### Option A: Install via pip (Recommended for Python environment)
```bash
pip install mcp-server-datahub
```

### Option B: Run dynamically via uvx
```bash
uvx mcp-server-datahub
```

---

## 4. Environment Variables Configuration

Create or update `.env` in the repository root:

```env
# DataHub GMS Backend Endpoint (Default local port: 8080 or 9002 frontend proxy)
DATAHUB_GMS_URL=http://localhost:8080

# (Optional) DataHub GMS Bearer Token if token auth is enabled
DATAHUB_GMS_TOKEN=

# Enable/Disable DataHub MCP integration in FastAPI
DATAHUB_MCP_ENABLED=true
```

> [!NOTE]
> **Authentication Note**: Because local DataHub Core instances or hackathon sandboxes may not allow Personal Access Token (PAT) generation, `DATAHUB_GMS_TOKEN` is optional. If left blank, unauthenticated GMS calls are attempted.

---

## 5. Local Development Setup

1. **Verify DataHub Core is running locally**:
   Ensure DataHub Core is active (e.g. `http://localhost:9002` web UI and `http://localhost:8080` GMS backend).

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install official DataHub MCP Server**:
   ```bash
   pip install mcp-server-datahub
   ```

---

## 6. How to Start Official DataHub MCP Server

Run the official MCP server process directly:

```bash
# Set environment variables
export DATAHUB_GMS_URL="http://localhost:8080"
export DATAHUB_GMS_TOKEN=""

# Run official server
mcp-server-datahub
```

Or via `uvx`:
```bash
uvx mcp-server-datahub
```

---

## 7. How to Test the Integration

### A. Python Verification Command
Run the following inline test script:

```bash
python -c "import backend.datahub as dh; print('Status:', dh.get_status()); print('Asset Context:', dh.get_asset_context('vehicle_health_features'))"
```

---

## 8. FastAPI Test Endpoints

Start the FastAPI server:
```bash
uvicorn backend.main:app --reload --port 8000
```

Available REST Endpoints:

### 1. Health Status Endpoint
```bash
curl -s http://localhost:8000/api/datahub/status
```
**Sample Output**:
```json
{
  "mcp_enabled": true,
  "mcp_connected": true,
  "datahub_connected": true,
  "gms_url": "http://localhost:8080",
  "error": null
}
```

### 2. Normalized Asset Context Endpoint
```bash
curl -s http://localhost:8000/api/datahub/asset/vehicle_health_features
```
**Sample Output**:
```json
{
  "asset": "vehicle_health_features",
  "description": null,
  "owners": [],
  "schema_fields": [],
  "upstream": [],
  "downstream": []
}
```

### 3. Prepared FleetGuard Context Endpoint (for AWS Bedrock)
```bash
curl -s http://localhost:8000/api/datahub/fleetguard-context/vehicle_health_features
```

---

## 9. Known Authentication Limitation

- **No PAT Support**: In DataHub Core instances where Personal Access Token generation is unavailable, `DATAHUB_GMS_TOKEN` remains empty.
- **Sanitized Error Handling**: If DataHub GMS or MCP Server is unreachable, FastAPI endpoints return structured `mcp_connected: false` state with sanitized error messages instead of failing or faking data.

---

## 10. How This Connects to AWS Bedrock

```
1. Telemetry Alert Trigger (e.g. car-003 LiDAR vibration anomaly)
       │
       ▼
2. FastAPI calls `get_fleetguard_context("car-003_lidar_sensor")`
       │
       ▼
3. DataHub MCP Server returns Schema, Upstream Hardware Supplier, Maintainer Owner, Downstream ML RUL Model
       │
       ▼
4. Context Payload injected into AWS Bedrock LLM Prompt
       │
       ▼
5. Bedrock produces Root Cause Report + Maintenance Remediation Plan
```
