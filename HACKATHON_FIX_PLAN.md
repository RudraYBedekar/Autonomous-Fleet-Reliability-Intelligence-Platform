# FleetGuard Hackathon Fix Plan

**Current judge score:** 6.0 / 10  
**Target after fixes:** 7.5–8.2 / 10  
**Recommendation:** Submit after completing **P0** and **P1** items below.

This document lists every fix needed, in priority order, with exact files and what to change.

---

## Priority Legend

| Priority | Meaning |
|---|---|
| **P0** | Must fix before submission — judges will catch these immediately |
| **P1** | High impact — strongly improves DataHub / agent credibility |
| **P2** | Important polish — improves reliability and demo quality |
| **P3** | Nice to have — low ROI for judging score |

---

## P0 — Critical (Do First)

### P0-1. Replace broken MCP reads with verified DataHub SDK reads

**Problem:** All MCP tool calls (`search`, `get_schema`, `get_lineage`, `get_entity`) time out. The app hides this with hardcoded fallback metadata in `get_fleetguard_context()`.

**Why judges care:** They will ask to see live lineage. If MCP fails and fallback fills in fake data, you lose trust on the core hackathon requirement.

**Files to change:**

| File | What to change |
|---|---|
| `backend/datahub/context_service.py` | Remove or gate hardcoded fallback blocks (lines ~131–160). Add SDK read path using `DataHubGraph` for schema, lineage, ownership. Return `source: "live" \| "unavailable"` in payload. |
| `backend/datahub/mcp_client.py` | Either fix MCP handshake (initialize → tools/list → tools/call) or demote MCP to optional and document SDK as primary read path. |
| `backend/datahub/models.py` | Add fields like `metadata_source`, `datahub_live`, `fallback_used` to response models. |

**Exact fix:**

1. Create `backend/datahub/graph_reader.py` (new file) with:
   - `get_dataset_properties(urn)`
   - `get_ownership(urn)`
   - `get_upstream_lineage(urn)`
   - `get_downstream_lineage(urn)` via graph API or lineage endpoint
2. Update `get_asset_context()` to call graph reader first, MCP second (optional).
3. Delete silent fallback that injects fake schema/lineage unless `DEMO_FALLBACK_ENABLED=true`.

**Acceptance test:**

```bash
# With DataHub running on :8080 and ingest done:
curl http://127.0.0.1:8000/api/datahub/fleetguard-context/vehicle_health_features
# Must return non-empty lineage WITHOUT fallback flag when GMS is up
```

**Estimated effort:** 4–8 hours  
**Score impact:** +0.8 to +1.2

---

### P0-2. Remove misleading “success” when DataHub write-back did not happen

**Problem:** `emit_investigation_result()` returns `success: true` even when `datahub_written: false`. UI shows “Synced to GMS” too easily.

**Files to change:**

| File | What to change |
|---|---|
| `backend/datahub/writeback.py` | Return `success: false` when GMS unreachable. Separate `attempted`, `datahub_written`, `mode`, `error`. Do not hardcode default `affected_models` in payload (line ~47). |
| `backend/services/fleetguard_agent.py` | Stage 5 status should be `FAILED` or `OFFLINE`, not `COMPLETED`, when `datahub_written` is false. |
| `frontend/src/components/FleetGuardModal.jsx` | Show red/amber badge for offline write-back; only show green “Synced to GMS” when `writeback.datahub_written === true`. |

**Acceptance test:**

```bash
# Stop DataHub, run investigate:
curl -X POST http://127.0.0.1:8000/api/fleetguard/investigate \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"car-003"}'
# writeback.datahub_written must be false; stage 5 must not say COMPLETED
```

**Estimated effort:** 2–3 hours  
**Score impact:** +0.3 to +0.5

---

### P0-3. Fix FleetGuardModal hardcoded API URL

**Problem:** Modal calls `http://localhost:8000/api/fleetguard/investigate` directly. Breaks on EC2/nginx/production.

**Files to change:**

| File | What to change |
|---|---|
| `frontend/src/components/FleetGuardModal.jsx` | Replace hardcoded URL with `apiUrl('/api/fleetguard/investigate')` from `../api`. |
| `frontend/src/api.js` | No change needed if `apiUrl()` already returns relative paths. |

**Acceptance test:** Deploy behind nginx on EC2; agent modal must work at `http://<EC2_IP>/` without localhost.

**Estimated effort:** 15 minutes  
**Score impact:** +0.2 (deployment reliability)

---

### P0-4. Unify DataHub GMS URL defaults

**Problem:** `mcp_client.py` defaults to `http://127.0.0.1:18080`; `writeback.py` and `.env.example` use `http://localhost:8080`. Status shows disconnected while write-back succeeds.

**Files to change:**

| File | What to change |
|---|---|
| `backend/datahub/mcp_client.py` | Default to `http://localhost:8080` (same as `.env.example`). |
| `backend/routers/datahub.py` | Error fallback URL should read from env, not hardcoded `18080`. |
| `docs/DATAHUB_MCP_SETUP.md` | Mark SSH tunnel as optional EC2 path; local docker as primary judge path. |
| `.env.example` | Single canonical `DATAHUB_GMS_URL=http://localhost:8080`. |

**Estimated effort:** 30 minutes  
**Score impact:** +0.2

---

### P0-5. Fix Copilot “Run RCA” response field mismatch

**Problem:** `CopilotPanel.jsx` reads `data.ai_report` but `/api/ai/diagnose/{id}` returns `ai_analysis`.

**Files to change:**

| File | What to change |
|---|---|
| `frontend/src/components/CopilotPanel.jsx` | Use `data.ai_analysis` (or backend alias both fields). |
| `backend/routers/ai.py` | Optionally return `ai_report: agent_res["root_cause_summary"]` for backward compatibility. Remove dead unreachable code after line 242. |

**Estimated effort:** 20 minutes  
**Score impact:** +0.1 (demo polish)

---

## P1 — High Impact (Strongly Recommended)

### P1-1. Add real Production ML incident: schema drift scenario

**Problem:** No `battery_temperature → battery_temp_c` (or similar) drift story. Production ML Agents track requires a credible silent breakage scenario.

**Files to change:**

| File | What to change |
|---|---|
| `backend/datahub/ingest_sample.py` | Ingest schema with field `battery_temperature`. Add downstream feature dataset + RUL/anomaly model lineage. Add second ingest state or migration script simulating rename to `battery_temp_c`. |
| `backend/services/fleetguard_agent.py` | Accept alert type like `schema_drift`. Compare live telemetry field names vs DataHub schema. Include drift in Bedrock prompt. |
| `backend/routers/fleetguard.py` | Add optional `incident_type: schema_drift` on investigate request. |
| `README.md` | Document the exact demo scenario step-by-step. |

**Suggested lineage to ingest:**

```
fleet.telemetry.raw
  → vehicle_telemetry
  → telemetry_cleaned
  → vehicle_health_features   (schema includes battery_temperature)
  → rul_predictor_model
  → anomaly_detector_model
  → Fleet Reliability Dashboard (dataset or dataJob)
```

**Acceptance test:** Agent investigation on schema drift must cite missing/renamed field and downstream models from **live** DataHub read (not fallback).

**Estimated effort:** 1 day  
**Score impact:** +0.6 to +0.9

---

### P1-2. Make write-back persist real investigation knowledge

**Problem:** Write-back updates `datasetProperties.customProperties` only. Tags like `#fleetguard_investigated` are listed in JSON but not emitted as DataHub Tag aspects. No incident history retrieval.

**Files to change:**

| File | What to change |
|---|---|
| `backend/datahub/writeback.py` | Emit proper aspects: `globalTags`, `structuredProperties` or `datasetProperties` + `institutionalMemory`/custom aspect for incident record. Include `incident_id`, `timestamp`, `vehicle_id`, `root_cause`, `confidence`, `remediation`, `status`. |
| `backend/routers/fleetguard.py` | Add `GET /api/fleetguard/investigations/{vehicle_id}` returning history from DataHub or local store. |
| `backend/datahub/models.py` | Add `InvestigationRecord` pydantic model. |

**Acceptance test:** After investigate, open DataHub UI → `vehicle_health_features` → verify tags/properties/incident note visible. Second agent call can retrieve prior investigation.

**Estimated effort:** 4–6 hours  
**Score impact:** +0.4 to +0.6

---

### P1-3. Prove Bedrock in the demo path (or disclose fallback clearly)

**Problem:** Without AWS credentials, agent uses canned diagnostic text that looks like AI output. Judges may think Bedrock ran.

**Files to change:**

| File | What to change |
|---|---|
| `backend/services/bedrock_client.py` | Remove dead/unreachable code (lines ~160–168). Return structured `{ text, model_id, source: "bedrock"|"fallback" }`. |
| `backend/services/fleetguard_agent.py` | If Bedrock fails, prefix response with `[OFFLINE REASONING — Bedrock unavailable]`. Pass `reasoning_source` to frontend. |
| `deploy/fleet-api.service` | Load env file: `EnvironmentFile=@REPO_ROOT@/.env` |
| `deploy/ec2-setup.sh` | Document IAM role for Bedrock; copy `.env.example` → `.env`. |
| `.env.example` | Use one valid model ID: `BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0` |

**Acceptance test:** Logs show `[Bedrock Success]` on EC2 with IAM role; UI shows model ID used.

**Estimated effort:** 3–6 hours  
**Score impact:** +0.3 to +0.5

---

### P1-4. Complete DataHub docker-compose for judges

**Problem:** `deploy/docker-compose.datahub.yml` only has GMS + frontend; missing MySQL and dependencies. Judges cannot reliably start DataHub from repo.

**Files to change:**

| File | What to change |
|---|---|
| `deploy/docker-compose.datahub.yml` | Use official DataHub quickstart compose OR add mysql, kafka, elasticsearch, schema-registry per DataHub docs. |
| `README.md` | Replace optional note with working one-command startup + wait time + ingest command. |
| `deploy/ec2-setup.sh` | Optional flag to start DataHub compose on same EC2 box. |

**Acceptance test:**

```bash
docker compose -f deploy/docker-compose.datahub.yml up -d
# wait for healthy
python -m backend.datahub.ingest_sample
# open http://localhost:9002 — entities visible
```

**Estimated effort:** 4–8 hours  
**Score impact:** +0.3 to +0.5

---

## P2 — Important Polish

### P2-1. Auto-trigger agent on critical alerts (optional but strong)

**Problem:** Agent only runs when user clicks chip/modal. Not truly autonomous.

**Files to change:**

| File | What to change |
|---|---|
| `backend/services/generator.py` | On new critical alert, optionally enqueue investigation (debounced per vehicle). |
| `backend/services/fleetguard_agent.py` | Add `investigate_if_critical(vehicle_id, alert)` guard to avoid spam. |
| `frontend/src/App.jsx` or `AlertsPanel.jsx` | Toast/modal when auto-investigation completes. |

**Estimated effort:** 3–4 hours  
**Score impact:** +0.2 to +0.4 (agent track)

---

### P2-2. Add missing README endpoint or remove false claim

**Problem:** README documents `POST /api/datahub/writeback` but route does not exist in `backend/routers/datahub.py`.

**Files to change:**

| File | What to change |
|---|---|
| `backend/routers/datahub.py` | Add `POST /writeback` wrapping `emit_investigation_result()`, OR |
| `README.md` | Remove endpoint and document write-back only via `/api/fleetguard/investigate` stage 5. |

**Estimated effort:** 30–60 minutes

---

### P2-3. Show DataHub status in frontend

**Problem:** DataHub only visible inside agent modal. Judges may miss it.

**Files to change:**

| File | What to change |
|---|---|
| `frontend/src/components/CopilotPanel.jsx` or `FleetPanel.jsx` | Small badge: DataHub Connected / Offline from `GET /api/datahub/status`. |
| `frontend/src/components/FleetGuardModal.jsx` | Show `metadata_source: live|fallback` on stage 2. |

**Estimated effort:** 2 hours  
**Score impact:** +0.2 (UX clarity)

---

### P2-4. Wire `/api/ai/ask` to DataHub for vehicle-specific ML context

**Problem:** Copilot chat does not use DataHub at all; only agent loop does.

**Files to change:**

| File | What to change |
|---|---|
| `backend/routers/ai.py` | When query mentions diagnose/lineage/models, call `get_fleetguard_context("vehicle_health_features")` and inject into Bedrock prompt. |

**Estimated effort:** 2–3 hours  
**Score impact:** +0.2

---

### P2-5. Add minimal tests for judge-critical paths

**Problem:** `pytest` in requirements but zero tests.

**Files to create:**

| File | What to test |
|---|---|
| `tests/test_fleetguard_agent.py` | Investigate returns 5 stages; writeback honest flags |
| `tests/test_datahub_context.py` | No fallback when `DEMO_FALLBACK_ENABLED=false` |
| `tests/test_ai_ask.py` | `/api/ai/ask` returns 200 for car-003 |

**Estimated effort:** 3–4 hours  
**Score impact:** +0.1 (engineering quality)

---

## P3 — Low Priority (Skip Unless Time Remains)

| Item | File(s) | Notes |
|---|---|---|
| Remove unused `langchain` deps | `requirements.txt` | Cleanup only |
| Delete legacy `dashboard.py` clutter | `legacy/`, root duplicates | No judge impact |
| More map/glassmorphism UI | `frontend/` | Low ROI |
| Kafka integration for lineage | `streaming/` | High effort, low score gain |
| Passenger manifest UI details | `CopilotPanel.jsx` | Orthogonal to hackathon tracks |

---

## File-by-File Change Checklist

Use this as a execution checklist:

### Backend

- [ ] `backend/datahub/context_service.py` — Remove silent fallback; add SDK reads; expose `metadata_source`
- [ ] `backend/datahub/graph_reader.py` — **NEW** — DataHubGraph read helpers
- [ ] `backend/datahub/mcp_client.py` — Fix MCP protocol or mark optional; unify default URL
- [ ] `backend/datahub/writeback.py` — Honest success flags; real tag aspects; incident record
- [ ] `backend/datahub/ingest_sample.py` — Full ML lineage + schema fields + drift scenario
- [ ] `backend/datahub/models.py` — Add investigation + metadata source models
- [ ] `backend/services/fleetguard_agent.py` — Schema drift support; honest Bedrock fallback; fix stage 5 status
- [ ] `backend/services/bedrock_client.py` — Remove dead code; structured response with source
- [ ] `backend/routers/fleetguard.py` — Add investigations history endpoint
- [ ] `backend/routers/datahub.py` — Add writeback route OR update docs
- [ ] `backend/routers/ai.py` — Fix diagnose response; remove dead code; optional DataHub in ask
- [ ] `backend/main.py` — No change expected

### Frontend

- [ ] `frontend/src/components/FleetGuardModal.jsx` — Use `apiUrl()`; honest write-back badge; show metadata source
- [ ] `frontend/src/components/CopilotPanel.jsx` — Fix `ai_analysis` field; DataHub status badge
- [ ] `frontend/src/components/AlertsPanel.jsx` — Optional auto-investigate trigger UI

### Deploy / Docs

- [ ] `deploy/docker-compose.datahub.yml` — Complete working DataHub stack
- [ ] `deploy/fleet-api.service` — `EnvironmentFile=` for `.env`
- [ ] `deploy/ec2-setup.sh` — Bedrock IAM note; optional DataHub startup
- [ ] `.env.example` — Canonical vars; one Bedrock model ID
- [ ] `README.md` — Accurate endpoints; judge demo script; no false MCP claims until fixed
- [ ] `docs/DATAHUB_MCP_SETUP.md` — Local docker primary; tunnel optional

### Tests

- [ ] `tests/test_fleetguard_agent.py` — **NEW**
- [ ] `tests/test_datahub_context.py` — **NEW**

---

## What NOT To Change

These are already good enough:

- Fleet telemetry simulation (`backend/services/generator.py`)
- WebSocket live map pipeline
- Rule-based alerts engine
- Fleet manifest / charging station logic
- Apache 2.0 `LICENSE`
- Overall React + FastAPI structure
- Agent modal 5-stage UX concept (keep, just make honest)

---

## Suggested Work Order (1–2 Days)

### Day 1 — Make DataHub real

1. P0-4 Unify GMS URL  
2. P0-1 SDK read path + remove fallback  
3. P0-2 Honest write-back  
4. P1-2 Proper write-back aspects  
5. P1-1 Schema drift ingest + agent logic  

### Day 2 — Make demo judge-proof

1. P0-3 Fix modal API URL  
2. P0-5 Fix RCA field  
3. P1-3 Bedrock on EC2 + honest fallback labeling  
4. P1-4 Complete docker-compose  
5. P2-3 DataHub status badge in UI  
6. Record 3-minute demo using README script  

---

## Demo Recording Checklist (After Fixes)

Before recording video, verify ALL of these pass:

- [ ] `docker compose -f deploy/docker-compose.datahub.yml up -d` works
- [ ] `python -m backend.datahub.ingest_sample` succeeds
- [ ] `GET /api/datahub/status` → `datahub_connected: true`
- [ ] `GET /api/datahub/fleetguard-context/vehicle_health_features` → lineage from **live** source, not fallback
- [ ] `POST /api/fleetguard/investigate` → stage 5 `datahub_written: true`
- [ ] DataHub UI at `:9002` shows lineage + updated properties after investigate
- [ ] Agent modal works on EC2 URL (not localhost)
- [ ] Bedrock shows `[Bedrock Success]` OR UI clearly says offline reasoning
- [ ] Schema drift scenario demonstrable in video narration

---

## Score Projection

| Milestone | Expected score |
|---|---|
| Current state | **6.0 / 10** |
| After P0 only | **6.8–7.2 / 10** |
| After P0 + P1 | **7.5–8.2 / 10** |
| After P0 + P1 + P2 | **8.0–8.5 / 10** |

Winner/finalist range (8.5+) requires **live MCP or SDK reads with no fake fallback**, **schema drift demo**, and **verified write-back visible in DataHub UI**.

---

## Quick Reference: Current Bugs → Fix Location

| Bug | Fix in |
|---|---|
| MCP tools timeout | `mcp_client.py` or replace with `graph_reader.py` |
| Fake lineage when offline | `context_service.py` lines 131–160 |
| Write-back success when failed | `writeback.py` return logic |
| Modal broken on EC2 | `FleetGuardModal.jsx` line 14 |
| GMS URL mismatch 18080 vs 8080 | `mcp_client.py`, `.env.example` |
| Run RCA empty response | `CopilotPanel.jsx` + `ai.py` |
| README writeback route missing | `datahub.py` or `README.md` |
| No schema drift | `ingest_sample.py` + `fleetguard_agent.py` |
| Bedrock canned text looks real | `fleetguard_agent.py` + `bedrock_client.py` |
| docker-compose incomplete | `deploy/docker-compose.datahub.yml` |
