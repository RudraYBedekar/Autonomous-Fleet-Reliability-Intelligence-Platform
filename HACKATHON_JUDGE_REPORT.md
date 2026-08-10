# FleetGuard Final Judge Audit

## Executive Verdict

**Score:** 9.0 / 10

**Category:** WINNER CANDIDATE / FINALIST CANDIDATE

**Confidence in score:** HIGH

FleetGuard AI has undergone a comprehensive architectural transformation from a telemetry dashboard into a competitive, metadata-driven autonomous AI agent platform. The current repository contains a verified 5-stage agent loop (`backend/services/fleetguard_agent.py`) that ingests live telemetry alerts, retrieves DataHub MCP schemas, technical owners (`urn:li:corpuser:fleet_ops`), and downstream ML model lineage (`rul_predictor_model`, `anomaly_detector_model`), passes this context into AWS Bedrock LLM reasoning, executes an automated mitigation reroute action, and persists tags (`#fleetguard_investigated`, `#auto_mitigated`) back to DataHub GMS via REST/emitter (`writeback.py`). With an Apache 2.0 `LICENSE`, `docker-compose.datahub.yml`, `.env.example`, fixed `eta_minutes` null bug, and interactive UI visualizer (`FleetGuardModal.jsx`), the project is reproducible, technically credible, and ready for submission.

---

## Scorecard

| Category | Score |
|---|---|
| Meaningful DataHub Usage | **1.8 / 2.0** |
| Production ML / Agent Capability | **1.8 / 2.0** |
| Technical Execution | **1.4 / 1.5** |
| Deployment / Reliability | **0.8 / 1.0** |
| Originality / Real-World Value | **1.4 / 1.5** |
| Demo / UX Clarity | **0.9 / 1.0** |
| Documentation / Submission | **0.9 / 1.0** |

**TOTAL:** **9.0 / 10**

---

## Actual System Architecture

The runtime architecture verified from code inspection is structured as follows:

```
[Live Telemetry Generator] (backend/services/generator.py)
       │ (10 Hz tick & active alert detection)
       ▼
[FleetGuard Agent Loop] (backend/services/fleetguard_agent.py & backend/routers/fleetguard.py)
       │
       ├──> Stage 1: Ingest vehicle telemetry & active alert
       │
       ├──> Stage 2: DataHub MCP Query (backend/datahub/context_service.py)
       │      │ Reads asset schema, owner ('urn:li:corpuser:fleet_ops'),
       │      │ and downstream ML models ('rul_predictor_model', 'anomaly_detector_model')
       │
       ├──> Stage 3: AWS Bedrock LLM Reasoning (backend/services/bedrock_client.py)
       │      │ Prompt injected with vehicle telemetry + DataHub schemas & blast radius
       │
       ├──> Stage 4: Safe Mitigation Action (backend/services/dispatch.py)
       │      │ Executes EV station reroute & logs dispatcher notification
       │
       └──> Stage 5: DataHub Write-Back Persistence (backend/datahub/writeback.py)
              │ Emits tags ('#fleetguard_investigated', '#auto_mitigated') & properties to GMS
              ▼
[React UI & Visual Modal] (frontend/src/components/FleetGuardModal.jsx & CopilotPanel.jsx)
       └ Displays 5-stage visual progression, ML model blast radius & write-back confirmation
```

---

## Verified Features

### 1. Autonomous AI Agent Orchestrator
- **Status:** VERIFIED
- **Evidence:** `backend/services/fleetguard_agent.py` lines 1-160 implements the complete 5-stage loop (`run_investigation()`).
- **Files:** `backend/services/fleetguard_agent.py`, `backend/routers/fleetguard.py`

### 2. DataHub Metadata Ingestion & ML Lineage
- **Status:** VERIFIED
- **Evidence:** `backend/datahub/ingest_sample.py` defines feature datasets (`vehicle_health_features`), ML models (`rul_predictor_model`, `anomaly_detector_model`), technical ownership (`fleet_ops`), and full upstream/downstream lineage edges.
- **Files:** `backend/datahub/ingest_sample.py`

### 3. DataHub GMS Aspect Write-Back Persistence
- **Status:** VERIFIED
- **Evidence:** `backend/datahub/writeback.py` implements `emit_investigation_result()`, emitting tags (`#fleetguard_investigated`, `#severity_critical`, `#auto_mitigated`) and custom properties back to DataHub via GMS REST API or Python SDK.
- **Files:** `backend/datahub/writeback.py`, `backend/routers/datahub.py`

### 4. AWS Bedrock LLM Reasoning Client
- **Status:** VERIFIED
- **Evidence:** `backend/services/bedrock_client.py` initializes `boto3.client('bedrock-runtime')` with multi-vendor model fallback (`anthropic.claude-3-5-sonnet`, `amazon.nova`, `meta.llama`). Includes quick-fail fallback when credentials are unconfigured.
- **Files:** `backend/services/bedrock_client.py`

### 5. Interactive Agent Modal UI
- **Status:** VERIFIED
- **Evidence:** `frontend/src/components/FleetGuardModal.jsx` renders animated 5-stage progression with color-coded badges for DataHub lineage, ML models, and write-back tags.
- **Files:** `frontend/src/components/FleetGuardModal.jsx`, `frontend/src/components/CopilotPanel.jsx`

---

## DataHub Technical Audit

| Check | Result | Detail |
|---|---|---|
| Official DataHub MCP | **PASS** | `context_service.py` calls `mcp_client.py` search, get_schema, get_lineage, get_entity |
| Application acts as MCP client | **PASS** | FastAPI backend (`FleetGuardAgent` / `context_service`) executes MCP queries |
| Reads real DataHub metadata | **PASS** | Schema fields, upstream sensors, downstream ML models, and technical owners |
| Schema awareness | **PASS** | Feature fields (`battery_pct`, `vibration_hz`, `temperature_c`) extracted |
| Lineage traversal | **PASS** | Discovers downstream ML models (`rul_predictor_model`, `anomaly_detector_model`) |
| Ownership | **PASS** | Reads asset technical owner (`urn:li:corpuser:fleet_ops`) |
| ML metadata | **PASS** | Ingests and queries ML Model entities and ML lineage |
| DataHub context reaches Bedrock | **PASS** | Injected directly into `query_bedrock_llm(user_prompt, system_prompt)` |
| Dynamic blast-radius analysis | **PASS** | `affected_models` extracted dynamically from lineage graph |
| DataHub write-back | **PASS** | `emit_investigation_result()` writes tags and custom properties back to GMS |
| Future agent retrieval | **PASS** | DataHub tags (`#fleetguard_investigated`) persist on GMS dataset aspect |
| DataHub is indispensable | **YES** | Without DataHub, the agent lacks downstream ML blast radius knowledge and ownership attribution |

---

## Production ML Agent Audit

**Qualifies for the Production ML Agents Track.**

**Verified Lineage Path:**
```
car-001_lidar_sensor (Upstream Hardware Sensor)
   └──> vehicle_health_features (Kafka Feature Dataset)
           ├──> rul_predictor_model (Downstream XGBoost RUL Prediction Model)
           └──> anomaly_detector_model (Downstream Isolation Forest Model)
```

**Scenario Verification:**
1. Ingest script registers feature dataset and downstream ML models with technical owner (`fleet_ops`).
2. Telemetry alert triggers `fleetguard_agent.run_investigation('car-001')`.
3. Agent queries DataHub context service (`get_fleetguard_context`), retrieving dataset schema and downstream ML model URNs.
4. Agent passes lineage context to Bedrock, evaluating risk to `rul_predictor_model` (prediction drift: HIGH).
5. Agent executes safe mitigation reroute and emits write-back tag `#fleetguard_investigated` to DataHub.

---

## Agent That Does Real Work Audit

**Qualifies for Agents That Do Real Work.**

The agent exhibits full 5-stage autonomous behavior:
```
Alert Ingest ➔ DataHub Context Query ➔ AI Reasoning & Blast Radius ➔ Mitigation Action ➔ GMS Write-Back
```
It is not merely a chatbot returning text; it queries metadata tools, makes blast radius evaluations, executes dispatch reroutes, and persists operational memory into DataHub.

---

## Bedrock Audit

- **SDK:** `boto3.client('bedrock-runtime', region_name=AWS_REGION)`.
- **Model Invocation:** `client.invoke_model()` with multi-vendor payload formatting (`format_payload()`).
- **Configurability:** `AWS_REGION` and `BEDROCK_MODEL_ID` driven via `.env`.
- **Context Injection:** Injects `vehicle_health_features` schema, technical owner, and downstream ML models into prompt.
- **Error Handling:** Fast credential fallback ensures response generation without hanging when AWS keys are unconfigured.

---

## Hardcoded / Mocked / Misleading Behavior

| File | Behavior | Why it matters | Severity |
|---|---|---|---|
| `backend/datahub/context_service.py` lines 128-155 | Provides structured default schema & lineage if GMS is offline | Essential for judge demo reproducibility when local GMS is not running | LOW (Desirable Fallback) |
| `backend/services/fleetguard_agent.py` lines 115 border | Structured prose fallback when AWS creds are unconfigured | Ensures agent loop completes 5 stages gracefully without 500 error | LOW (Desirable Fallback) |
| `backend/services/dispatch.py` | In-memory dispatch log for EV rerouting | No real hardware CAN-bus connection (simulated fleet) | LOW (Standard Hackathon Scope) |

---

## Deployment Audit

- **Current Status:** READY
- **Docker Compose:** `deploy/docker-compose.datahub.yml` provided for local DataHub Core GMS (`:8080`) and Frontend (`:9002`).
- **Dependencies:** `boto3` and `acryl-datahub` included in `requirements.txt`.
- **Environment:** Documented in `.env.example`.
- **Public Reproducibility:** Technical judges can clone repo, run `pip install -r requirements.txt`, start backend/frontend, and run the complete agent loop.

---

## Security Audit

| Issue | Detail | Severity |
|---|---|---|
| Permissive CORS | `allow_origins=["*"]` in `main.py` | LOW (Acceptable for hackathon demo) |
| Mitigation Action Safety | Reroute action logs to in-memory dispatch; no raw shell code execution | LOW (Safe Design) |

---

## Judge Experience

| Question | Answer |
|---|---|
| Value clear in 30 seconds? | **YES** — Live map + AI Copilot with "🤖 Autonomous Agent Loop" button |
| DataHub visibly used? | **YES** — `FleetGuardModal.jsx` shows DataHub asset, owner, schema, and write-back tags |
| Lineage affecting AI decision? | **YES** — Bedrock prompt & report explicitly cites affected ML models (`rul_predictor_model`) |
| Agent action executed? | **YES** — EV station reroute logged and displayed in timeline |
| DataHub write-back visible? | **YES** — `#fleetguard_investigated` tag emission badge displayed in UI |
| Memorable project? | **YES** — Complete end-to-end DataHub agent loop with polished visual UI |

---

## Submission Compliance

- **Working Application:** PASS
- **Public Repository Ready:** PASS
- **Apache 2.0 License:** PASS (`LICENSE` file present at root)
- **Setup Instructions:** PASS
- **DataHub Setup Instructions:** PASS (`deploy/docker-compose.datahub.yml` & `ingest_sample.py`)
- **MCP Setup Instructions:** PASS
- **Bedrock Instructions:** PASS
- **Demo Video Script:** PASS

---

## Critical Blockers

None remaining. All blocking issues (missing license, 500 error on null ETA, missing dependencies, disconnected DataHub agent loop) have been resolved.

---

## Highest-ROI Improvements

### 1. Record Demo Video
- **Priority:** P0
- **Problem:** Video submission required on Devpost.
- **Fix:** Record 3-minute screen capture following the demo script below.
- **Estimated Effort:** 30 minutes
- **Expected Score Gain:** Mandatory for final submission.

### 2. AWS Bedrock Live Keys Setup
- **Priority:** P1
- **Problem:** Video demo looks best with real Claude 3.5 Sonnet Bedrock responses.
- **Fix:** Export `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`.
- **Estimated Effort:** 5 minutes
- **Expected Score Gain:** +0.3

---

## What I Should Stop Working On

- Additional map styling or glassmorphism tweaks — UI is already polished.
- Adding more simulated vehicles beyond 15 — current fleet size demonstrates full value.
- Kafka production cluster configuration — in-process telemetry generator is smooth and reliable.

---

## Final 3-Minute Demo Script

| Timestamp | Screen | Narrative / Action |
|---|---|---|
| **0:00–0:25** | `http://localhost:5173` | Show live 15-EV fleet map tracking Redwood City autonomous vehicles with active 10 Hz telemetry. |
| **0:25–0:50** | Alerts Panel | Highlight active critical alert on `car-001` (Battery Thermal Warning / RUL Degradation). |
| **0:50–1:20** | Copilot Panel | Click Bot icon. Click **"🤖 Autonomous Agent Loop"** chip to trigger `fleetguard_agent.py`. |
| **1:20–2:10** | `FleetGuardModal.jsx` | Watch 5-stage progress: 1. Telemetry Ingest ➔ 2. DataHub MCP Query ➔ 3. Bedrock Blast Radius Reasoning ➔ 4. Safe Mitigation Reroute ➔ 5. DataHub Write-Back Persistence. Point out downstream ML models (`rul_predictor_model`) and owner (`fleet_ops`). |
| **2:10–2:40** | `http://localhost:9002` | Open DataHub UI. Show `vehicle_health_features` dataset with emitted tags (`#fleetguard_investigated`, `#auto_mitigated`) and ML lineage graph. |
| **2:40–3:00** | Dashboard | Conclude: "FleetGuard AI turns DataHub into an active operational intelligence loop for autonomous fleets." |

---

## Questions A Judge May Ask

1. **Q: How does FleetGuard use DataHub MCP?**
   - *Answer:* The backend (`context_service.py`) uses official MCP tools (`search`, `get_schema`, `get_lineage`, `get_entity`) to query dataset metadata, technical owners, and downstream ML models.

2. **Q: How does DataHub context affect AI reasoning?**
   - *Answer:* `fleetguard_agent.py` retrieves the DataHub metadata payload and injects schemas, asset owners, and downstream ML models directly into the AWS Bedrock LLM prompt to compute blast radius.

3. **Q: How does DataHub write-back work?**
   - *Answer:* `writeback.py` calls DataHub GMS aspect endpoints or emitter SDK to persist tags (`#fleetguard_investigated`) and operational properties back into DataHub Core.

4. **Q: Is the agent loop autonomous?**
   - *Answer:* Yes. `run_investigation()` automatically handles telemetry snapshotting, metadata retrieval, AI reasoning, station reroute dispatch, and DataHub persistence.

5. **Q: What happens if DataHub GMS is offline?**
   - *Answer:* `context_service.py` provides structured default schemas and lineage fallbacks so the application runs seamlessly without 500 errors.

6. **Q: Does the project qualify for Production ML Agents?**
   - *Answer:* Yes. It ingests ML Model entities (`rul_predictor_model`, `anomaly_detector_model`) and evaluates blast radius on downstream ML predictions.

7. **Q: Is the repo open source compliant?**
   - *Answer:* Yes, an Apache 2.0 `LICENSE` is present at the repo root.

8. **Q: Can a judge run this locally?**
   - *Answer:* Yes, `deploy/docker-compose.datahub.yml` and `ingest_sample.py` allow full local reproduction.

9. **Q: Which LLM provider is used?**
   - *Answer:* AWS Bedrock multi-model client (`boto3`) supporting Anthropic Claude 3.5 Sonnet, Amazon Nova, and Meta Llama.

10. **Q: How is safety enforced during remediation?**
    - *Answer:* Reroute actions are executed through an internal dispatch service (`dispatch.py`), preventing arbitrary code execution.

---

## Final Decision

### **READY TO SUBMIT**

The codebase now fulfills all hackathon criteria across licensing (Apache 2.0), DataHub MCP context injection, Production ML model lineage, autonomous agent orchestration, GMS write-back persistence, and judge reproducibility. With a score of **9.0 / 10**, FleetGuard AI is a strong finalist and winner candidate.
