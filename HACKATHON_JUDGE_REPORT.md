# FleetGuard Hackathon Judge Report

## Overall Score
**3.4 / 10**

## One-Sentence Verdict
This is a **polished fleet telemetry demo with Bedrock/chat scaffolding**, but **not a credible DataHub agent submission** — DataHub is sidecar API plumbing, not part of the agent loop, and the repo is **not submission-ready** (no Apache 2.0 license, broken copilot path, judge-unfriendly DataHub setup).

## Score Breakdown

| Category | Score |
|---|---|
| Meaningful DataHub Usage | **0.5 / 2.0** |
| Agent / Production ML Functionality | **0.4 / 2.0** |
| Technical Execution | **0.9 / 2.0** |
| Originality + Usefulness | **0.8 / 1.5** |
| Demo / UX | **0.4 / 1.0** |
| Submission Readiness | **0.3 / 1.5** |

---

## What Is Actually Working

Verified by reading code and running the backend locally (`uvicorn backend.main:app`):

| Capability | Evidence |
|---|---|
| FastAPI backend starts and serves fleet API | `backend/main.py` |
| 15-vehicle simulated telemetry @ 10 Hz | `backend/services/generator.py` |
| WebSocket live telemetry broadcast | `backend/routers/websockets.py` |
| Rule-based fleet alerts (battery, health, RUL, school zone, stall) | `backend/services/alerts.py` |
| Fleet manifest, charging stations, dispatch call/message (in-memory log) | `backend/routers/fleet.py`, `backend/services/dispatch.py` |
| React dashboard: map, fleet panel, alerts, copilot drawer | `frontend/src/App.jsx`, `FleetPanel`, `Map`, `AlertsPanel`, `CopilotPanel.jsx` |
| DataHub **status** endpoint (honest disconnected state when GMS down) | `backend/routers/datahub.py`, `backend/datahub/mcp_client.py` |
| DataHub context endpoints return **empty** metadata when GMS unreachable | `backend/datahub/context_service.py` — verified via `GET /api/datahub/fleetguard-context/vehicle_health_features` |
| Bedrock client code with multi-model retry | `backend/services/bedrock_client.py` — **UNVERIFIED success** (no AWS creds locally; logs show `Unable to locate credentials`) |
| Heuristic RCA engine (rule-based, not LLM) | `ml/rca_engine.py`, used in `backend/routers/ai.py` `/diagnose` |
| Sample DataHub ingest script (datasets + one upstream edge) | `backend/datahub/ingest_sample.py` — **UNVERIFIED end-to-end** (requires running DataHub + `acryl-datahub`, not in `requirements.txt`) |
| EC2 deploy script (nginx + systemd) | `deploy/ec2-setup.sh`, `deploy/nginx-fleet.conf`, `deploy/fleet-api.service` |

**Not working in the main application path (despite README claims):**

- Isolation Forest ML (`analytics_engine.py` only used by legacy `dashboard.py`, not FastAPI live path)
- DataHub-informed agent reasoning
- DataHub write-back
- Autonomous incident investigation loop (`FLEETGUARD_IMPLEMENTATION_PLAN.md` describes it; code does not exist)

---

## What Looks Strong to a Judge

1. **Live fleet simulation UX** — 15 EVs, map tracking, manifests, charging reroute logic, alerts panel. This is a real demo surface (`generator.py`, `App.jsx`, `Map.jsx`).

2. **Backend architecture is coherent** — FastAPI routers, Pydantic schemas, in-process generator vs optional Kafka, WebSocket fanout. Clean separation for a hackathon codebase.

3. **DataHub integration is attempted honestly when offline** — returns empty arrays / `datahub_connected: false` instead of inventing lineage (`context_service.py`, verified at runtime).

4. **Bedrock client is thoughtfully structured** — vendor-specific payload formatting, model fallback chain (`bedrock_client.py`).

5. **Deployment story exists** — one-box EC2 script with nginx reverse proxy for `/api` and `/ws` (`deploy/ec2-setup.sh`).

---

## What Would Cost Us Points

### CRITICAL

- **No Apache 2.0 `LICENSE` at repo root** — hackathon submission requirement; **BLOCKING**.
- **DataHub is not in the agent loop** — `get_fleetguard_context()` is only exposed via REST (`backend/routers/datahub.py`); **`backend/routers/ai.py` never imports or uses DataHub**. Removing DataHub would not change copilot/RCA behavior.
- **No DataHub write-back** — zero `emit`, tags, structured properties, incident records, or remediation persistence anywhere except one-way ingest in `ingest_sample.py`.
- **Judge cannot reproduce DataHub setup from repo alone** — no Docker Compose for DataHub, no bootstrap script for ML lineage/models, architecture depends on **developer laptop + SSH reverse tunnel** (`README.md`, `docs/DATAHUB_MCP_SETUP.md`).
- **`POST /api/ai/ask` returns HTTP 500** when Bedrock fails and vehicle has `eta_minutes: null` — verified locally: `unsupported format string passed to NoneType.__format__` at `backend/routers/ai.py` line 144.

### HIGH

- **MCP client is likely non-functional even with DataHub running** — `call_tool()` sends a single JSON-RPC `tools/call` over stdio with no MCP initialize/handshake, 5s timeout, and on failure returns misleading `success: datahub_connected` with empty `data` (`backend/datahub/mcp_client.py` lines 109–165). **UNVERIFIED** against live MCP server.
- **`mcp_connected: true` only means binary/uvx exists in PATH**, not that MCP tools actually work (`check_mcp_connection()`).
- **README overclaims** — "Agent Context Kit", "Isolation Forest", "metadata-aware RCA", "write-back" — not implemented in runnable paths.
- **Missing dependencies in `requirements.txt`** — `boto3` (used by Bedrock), `acryl-datahub` (used by ingest). Fresh `pip install -r requirements.txt` will break Bedrock and ingest.
- **No tests** — `pytest` listed in requirements, zero test files in repo.
- **Planned agent files never built** — no `fleetguard_agent.py`, `backend/routers/fleetguard.py`, `FleetGuardModal.jsx` (only in `FLEETGUARD_IMPLEMENTATION_PLAN.md`).

### MEDIUM

- **Production ML track unsupported** — ingest creates 3 datasets, one upstream edge; no ML model entities, no feature→model→deployment lineage, no schema drift scenario (`ingest_sample.py`).
- **RCA is hardcoded heuristics**, not DataHub/lineage-driven blast radius (`ml/rca_engine.py`).
- **Bedrock falls back to templated text** that looks like AI output (`backend/routers/ai.py` lines 126–188, 233–240) — judges may think LLM worked when it did not.
- **No `.env.example`** — env vars documented only in README/docs; `.env` gitignored.
- **Frontend shows zero DataHub** — no status badge, lineage panel, affected models, write-back proof (`CopilotPanel.jsx` only calls `/api/ai/*`).

### LOW

- Legacy/dead code clutter (`legacy/`, root-level duplicates, Streamlit `dashboard.py`).
- `langchain` / `langchain-openai` in requirements but unused in backend.
- Copilot welcome message uses markdown (`**`, backticks) while system prompt forbids markdown in responses.

---

## DataHub Integration Verdict

| Question | Answer |
|---|---|
| Uses official MCP/Agent Context Kit | **PARTIAL** — references `mcp-server-datahub`; **no Agent Context Kit code found** |
| Reads real DataHub metadata | **PARTIAL** — code path exists; **returns empty when GMS down**; MCP tool retrieval **UNVERIFIED** |
| Uses schema | **NO** (live path) — endpoints exist; not consumed by agent |
| Uses lineage | **NO** (live path) — same |
| Uses ownership | **NO** (live path) |
| Uses ML metadata | **NO** — no ML models ingested |
| Uses DataHub information in Bedrock reasoning | **NO** — `ai.py` never calls `context_service` |
| Writes results back to DataHub | **NO** |
| DataHub is essential to the application | **NO** |

**Why:** DataHub is implemented as a **standalone metadata API layer** (`backend/datahub/*`, `backend/routers/datahub.py`). The copilot, RCA, alerts, and fleet logic operate entirely on simulated telemetry + rule engines. The "FleetGuard context for Bedrock" endpoint is labeled **"prepared for future AWS Bedrock LLM context injection"** in `context_service.py` line 124 — that future step was never completed.

**Critical test answers:**

- **A. Does the app call DataHub?** YES for health/context REST endpoints; NO in the AI/agent workflow.
- **B. Official MCP / Agent Context Kit?** MCP attempted via subprocess; Agent Context Kit **not implemented**.
- **C. Application as MCP client?** YES in intent (`DataHubMCPClient` in FastAPI backend); reliability **UNVERIFIED**.
- **D. Tools referenced:** `search`, `get_schema`, `get_lineage`, `get_entity` (`context_service.py`).
- **E. Information retrieved:** datasets schema/lineage/owners — **when MCP works**; currently empty in testing.
- **F. Metadata affects AI reasoning?** **NO.**
- **G. Remove DataHub → lose capability?** **NO** for current demo behavior.
- **H. Write-back?** **NO.**
- **I. Write-back real or fake?** N/A — absent.
- **J. Retrievable by later agent?** **NO.**

---

## Production ML Agent Verdict

**Does not qualify for the Production ML Agents track.**

| Criterion | Status |
|---|---|
| ML/data assets in DataHub | **NO** — only generic datasets, no RUL/anomaly model URNs |
| Lineage created and queryable | **PARTIAL** — one edge: `car-001_lidar_sensor → vehicle_health_features` in ingest script only |
| Identify impacted downstream ML models | **NO** — `affected_models` filters downstream URNs containing "model"/"prediction" but nothing ingested matches |
| Silent production problem (schema drift) | **NO** — not implemented anywhere |
| Blast radius from DataHub lineage vs hardcoded lists | **NO** — RCA uses hardcoded sensor thresholds |
| Bedrock receives DataHub context | **NO** |
| Root cause / affected assets / models / owner / severity / confidence / remediation | **PARTIAL** — RCA returns root cause + confidence + action from heuristics only; no DataHub-derived affected models or owners |
| Safe action + validation + DataHub record | **NO** |

The fleet has simulated RUL (`trip_insights.py`) and rule alerts, but that is **not** an ML production lineage story in DataHub.

---

## Agents That Do Real Work Verdict

**Does not qualify.** This is primarily:

```
user question → telemetry/manifest context string → Bedrock (or template fallback) → text
```

What is missing from a real agent loop:

- No autonomous trigger on alert → investigate
- No tool-driven DataHub queries during reasoning
- No action selection/execution beyond in-memory dispatch log (`dispatch.py`)
- No validation step
- No persistence of investigation results

The closest thing to "action" is **Run RCA** in the copilot, which calls `/api/ai/diagnose/{id}` → heuristic `RootCauseAnalyzer` + optional Bedrock prose. That is **diagnostics chatbot behavior**, not an agent.

---

## Fake / Hardcoded / Demo-Only Behavior

| Location | Behavior |
|---|---|
| `ml/rca_engine.py` | Entire RCA is hardcoded if/else rules with fixed confidence scores (50–99) |
| `backend/routers/ai.py` lines 126–188 | Template "AI" responses when Bedrock fails — fleet brief, battery analysis, passenger summary |
| `backend/routers/ai.py` lines 216–222 | Diagnose picks sensor type from simple battery/health thresholds, passes **fixed** temp/voltage/vibration values (65.0, 11.5, 1.4) |
| `backend/routers/ai.py` line 273 | Hardcoded `"Operational Readiness: 98.4% fleet health index"` in fleet brief fallback |
| `backend/services/trip_insights.py` | RUL is distance-based heuristic, not ML |
| `backend/services/alerts.py` | Rule thresholds only (battery < 15%, health < 70%, etc.) |
| `backend/services/generator.py` | Simulated telemetry — not real fleet/Kafka in default mode |
| `backend/services/dispatch.py` | "Call vehicle" logs to in-memory list; no telephony integration |
| `ml/anomaly_detector.py` | Simple threshold heuristics; **not wired** into FastAPI live path |
| `analytics_engine.py` | Isolation Forest exists but only used by legacy Streamlit `dashboard.py` |
| `backend/datahub/mcp_client.py` lines 159–165 | Silent empty success when MCP subprocess fails |
| `FLEETGUARD_IMPLEMENTATION_PLAN.md` | Describes features (agent orchestrator, write-back, FleetGuardModal) **not present in code** |

**Hardcoded lineage:** none masquerading as live DataHub data — when offline, endpoints correctly return empty arrays (not fake lineage).

---

## Deployment Risks

| Risk | Detail |
|---|---|
| **Localhost DataHub dependency** | Default `DATAHUB_GMS_URL=http://127.0.0.1:18080` expects SSH tunnel from EC2 to developer Windows machine |
| **Judge laptop must stay online** | Reverse tunnel architecture in README — EC2 backend useless for DataHub without external machine |
| **No in-repo DataHub bootstrap** | No docker-compose, no quickstart DataHub Core for judges |
| **MCP startup** | Requires `mcp-server-datahub` or `uvx` on EC2; MCP protocol implementation may fail even if binary exists |
| **Bedrock credentials** | No IAM role setup in `fleet-api.service`; no AWS env in deploy script; falls back to templates |
| **Missing pip deps** | `boto3`, `acryl-datahub` not in `requirements.txt` |
| **Copilot 500 bug** | Primary demo flow breaks without Bedrock + null ETA |
| **CORS** | Permissive `allow_origins=["*"]` — not a demo blocker but sloppy |
| **EC2 systemd** | No `.env` loading in `fleet-api.service` — DataHub/Bedrock env vars won't apply unless manually exported |

---

## README / Repository Audit

| Check | Result |
|---|---|
| Apache 2.0 license | **FAIL** — no `LICENSE` file found |
| Complete setup | **FAIL** — missing deps, no `.env.example`, no frontend start in README quick guide |
| DataHub setup | **PARTIAL** — docs exist (`docs/DATAHUB_MCP_SETUP.md`) but judge-hostile tunnel architecture |
| MCP setup | **PARTIAL** — pip install mentioned; no verified working MCP invocation |
| Bedrock setup | **FAIL** — not in requirements; no IAM/credential guide in deploy path |
| Demo scenario | **FAIL** — no step-by-step incident/lineage/write-back scenario |
| Architecture explanation | **PASS** — diagram in README (overstates integration depth) |
| Public-judge reproducibility | **FAIL** — depends on private infra (SSH tunnel, AWS creds, local DataHub) |

---

## Top 5 Things To Fix Before Submission

### 1.

**Priority:** P0  
**Problem:** DataHub not connected to agent/RCA flow  
**Why judges care:** This is a DataHub agent hackathon; sidecar REST endpoints alone will lose.  
**Exact fix:** Build `fleetguard_agent.py` orchestrator: alert → `get_fleetguard_context()` → Bedrock with structured JSON → optional safe action → DataHub emit. Wire into `/api/ai/diagnose` and new `/api/fleetguard/investigate`.  
**Files likely involved:** new `backend/services/fleetguard_agent.py`, `backend/routers/fleetguard.py`, `backend/routers/ai.py`, `backend/main.py`  
**Estimated effort:** 1–2 days  
**Expected score improvement:** +2.0–2.5 total

### 2.

**Priority:** P0  
**Problem:** No Apache 2.0 LICENSE  
**Why judges care:** Explicit submission requirement — disqualifying if missing.  
**Exact fix:** Add root `LICENSE` (Apache 2.0) and reference in README.  
**Files likely involved:** `LICENSE`, `README.md`  
**Estimated effort:** 10 minutes  
**Expected score improvement:** +0.3 (submission readiness)

### 3.

**Priority:** P0  
**Problem:** No ML lineage / schema drift / write-back story  
**Why judges care:** Production ML Agents track requires end-to-end lineage and blast-radius reasoning.  
**Exact fix:** Extend `ingest_sample.py` with feature dataset, RUL model, anomaly model URNs, ownership, schema fields, downstream edges; add schema drift simulation; implement `emit_investigation_result()` writing tags/structured properties; surface in UI.  
**Files likely involved:** `backend/datahub/ingest_sample.py`, new write-back module, `CopilotPanel.jsx`  
**Estimated effort:** 1–2 days  
**Expected score improvement:** +1.5–2.0 total

### 4.

**Priority:** P1  
**Problem:** Judge-unfriendly DataHub deployment (SSH tunnel)  
**Why judges care:** If judges cannot run it, they cannot verify claims.  
**Exact fix:** Add `docker-compose.datahub.yml` or document self-contained DataHub on same EC2; change default `DATAHUB_GMS_URL` to co-located instance; remove tunnel requirement from primary path.  
**Files likely involved:** new compose file, `README.md`, `docs/DATAHUB_MCP_SETUP.md`, `deploy/ec2-setup.sh`  
**Estimated effort:** 4–8 hours  
**Expected score improvement:** +0.5–0.8

### 5.

**Priority:** P1  
**Problem:** Broken copilot + missing dependencies  
**Why judges care:** Primary demo interaction fails (verified 500 on `/api/ai/ask`).  
**Exact fix:** Fix `eta_minutes` None formatting; add `boto3`, `acryl-datahub` to `requirements.txt`; add `.env.example`; fix or replace MCP client with verified official protocol.  
**Files likely involved:** `backend/routers/ai.py`, `requirements.txt`, `backend/datahub/mcp_client.py`, `.env.example`  
**Estimated effort:** 2–4 hours  
**Expected score improvement:** +0.4–0.6

---

## What NOT To Spend Time On

- More glassmorphism / map polish — judges already see a nice fleet UI; it won't fix DataHub scoring.
- Legacy Streamlit `dashboard.py` cleanup — not in demo path.
- Kafka infrastructure unless you prove DataHub lineage from Kafka topics — high effort, low hackathon score impact.
- LangChain integration — unused; Bedrock boto3 client already exists.
- Adding more simulated vehicles beyond 15 — does not demonstrate metadata agent value.
- Passenger manifest UI details — orthogonal to hackathon tracks.

---

## Recommended 3-Minute Demo

The video **must prove** each item below — not describe it.

| Time | Action | Must show on screen |
|---|---|---|
| 0:00–0:15 | Open live app | Fleet map with moving EVs; title "FleetGuard AI" |
| 0:15–0:30 | Trigger incident | Vehicle alert (battery critical or health degraded) in alerts panel |
| 0:30–0:50 | DataHub UI | `localhost:9002` (or deployed DataHub): `vehicle_health_features` dataset with schema + lineage graph including ML models |
| 0:50–1:10 | App queries DataHub | DevTools/network or terminal: `GET /api/datahub/fleetguard-context/vehicle_health_features` returning **non-empty** schema, lineage, owner, affected_models |
| 1:10–1:35 | Agent investigation | Click "Investigate" / "Run RCA" — show response citing **DataHub-derived** downstream models and owner (not generic text) |
| 1:35–1:55 | Bedrock reasoning | Log or UI showing Bedrock model invoked; structured output: root cause, severity, confidence, remediation |
| 1:55–2:15 | Blast radius | Explicit list: affected feature dataset + RUL model + anomaly model from lineage |
| 2:15–2:35 | Agent action | Safe action executed (reroute, notify owner, tag asset) with confirmation |
| 2:35–2:50 | DataHub write-back | Refresh DataHub entity — new tag/structured property/incident note visible |
| 2:50–3:00 | Close | "Next agent can retrieve this investigation from DataHub" — show retrieved metadata |

**Current repo cannot film this demo truthfully** without building items in Top 5 Fixes #1 and #3.

---

## Winning Pitch

*(Only based on what actually exists today — honest version)*

> FleetGuard AI is a real-time autonomous EV fleet operations dashboard with simulated 15-vehicle telemetry, rule-based alerting, and an AWS Bedrock-powered copilot for vehicle search and heuristic root-cause diagnostics. The backend includes scaffolding for the official DataHub MCP server with health and metadata context APIs, but the live copilot does not yet consume DataHub metadata or write investigation results back.

Do **not** use the README pitch about "metadata-aware autonomous investigation" until fixes land.

---

## Final Recommendation

## **DO NOT SUBMIT UNTIL CRITICAL FIXES ARE DONE**

**Why:**

1. **Missing Apache 2.0 license** — blocking submission requirement.
2. **DataHub is not essential** to the running application — the core judge test fails.
3. **No agent loop, no write-back, no Production ML lineage story** — does not meet any hackathon track at finalist level.
4. **Primary copilot endpoint can 500** without AWS credentials — demo risk.
5. **Judge reproduction path is unrealistic** (SSH tunnel to developer laptop).

You have a **solid fleet simulation foundation** (~0.9/2.0 technical execution for the non-DataHub parts), but the **DataHub agent layer is ~20% built and 0% integrated**. Fixing P0 items #1–#3 could realistically move this into the **6.5–7.5** range before the video. As-is: **3.4/10 — weak submission, not ready.**
