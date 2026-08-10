"""
Tests for FleetGuard Autonomous Agent Investigation Loop.
"""

import pytest
from backend.services.fleetguard_agent import fleetguard_agent


def test_run_investigation_returns_5_stages():
    res = fleetguard_agent.run_investigation(vehicle_id="car-003")
    assert res["success"] is True
    assert res["vehicle_id"] == "car-003"
    assert len(res["stages"]) == 5

    stage_names = [s["name"] for s in res["stages"]]
    assert "Alert Ingestion & Telemetry Snapshot" in stage_names[0]
    assert "DataHub Metadata & Lineage Retrieval" in stage_names[1]
    assert "AI Blast Radius & Reasoning" in stage_names[2]
    assert "Safe Mitigation Action Execution" in stage_names[3]
    assert "DataHub Write-Back Persistence" in stage_names[4]


def test_investigation_writeback_honest_flags():
    res = fleetguard_agent.run_investigation(vehicle_id="car-001")
    wb = res["writeback"]
    assert "datahub_written" in wb
    assert "mode" in wb
    # If GMS is offline, status must be OFFLINE, not COMPLETED
    stage5 = res["stages"][4]
    if not wb["datahub_written"]:
        assert stage5["status"] == "OFFLINE"
    else:
        assert stage5["status"] == "COMPLETED"
