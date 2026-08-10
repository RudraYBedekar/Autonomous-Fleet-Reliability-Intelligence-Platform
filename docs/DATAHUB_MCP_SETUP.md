# DataHub GMS & MCP Server Setup & Reverse Tunnel Guide

This guide documents the integration of the **OFFICIAL DataHub MCP Server** (`acryldata/mcp-server-datahub`) and **DataHub GMS v1.7.0** using an **SSH Reverse Tunnel Architecture** for the **Build with DataHub Agent Hackathon**.

---

## 1. Architecture & Network Topology

```
Windows Dev Machine (Docker DataHub Core)
  - DataHub GMS Container: 0.0.0.0:8080 -> 8080 (acryldata/datahub-gms:v1.7.0)
  - DataHub Frontend: http://localhost:9002
                          │
                          │ SSH Reverse Tunnel: ssh -i key.pem -R 18080:localhost:8080 ubuntu@EC2
                          ▼
AWS EC2 Machine (FastAPI Backend)
  - Loopback Tunnel Port: http://127.0.0.1:18080
  - FastAPI Port: 8000
```

---

## 2. Environment Variables Configuration

Create or update `.env` in the repository root:

```env
# DataHub GMS Endpoint (Default for EC2 SSH Tunnel: http://127.0.0.1:18080)
# Local Dev Default: http://localhost:8080
DATAHUB_GMS_URL=http://127.0.0.1:18080

# (Optional) DataHub GMS Bearer Token
DATAHUB_GMS_TOKEN=

# Enable/Disable DataHub MCP integration in FastAPI
DATAHUB_MCP_ENABLED=true
```

---

## 3. How to Start the SSH Reverse Tunnel from Windows

Run this in your **Windows PowerShell**:

```powershell
ssh -i "path\to\your-key.pem" -R 18080:localhost:8080 ubuntu@100.29.80.157
```

---

## 4. Diagnostics & Testing Commands

### A. Run CLI Diagnostic Script (Backend import test)
```bash
python -m backend.datahub.check_connection
```
**Sample Output**:
```text
DataHub GMS URL: http://127.0.0.1:18080
Connected: true
MCP Connected: true
```

### B. Test REST Status Endpoint
```bash
curl -s http://127.0.0.1:8000/api/datahub/status
```
**Sample Response**:
```json
{
  "mcp_enabled": true,
  "mcp_connected": true,
  "datahub_connected": true,
  "datahub_gms_url": "http://127.0.0.1:18080",
  "error": null
}
```

### C. Test FleetGuard Bedrock Context Payload
```bash
curl -s http://127.0.0.1:8000/api/datahub/fleetguard-context/vehicle_health_features
```
