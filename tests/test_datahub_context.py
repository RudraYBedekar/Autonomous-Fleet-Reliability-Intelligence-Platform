"""
Tests for DataHub Context Service & Metadata Source Flagging.
"""

import pytest
from backend.datahub.context_service import get_fleetguard_context, get_status


def test_datahub_status_schema():
    status = get_status()
    assert hasattr(status, "datahub_connected")
    assert hasattr(status, "mcp_connected")
    assert hasattr(status, "datahub_gms_url")


def test_get_fleetguard_context_metadata_source():
    payload = get_fleetguard_context("vehicle_health_features")
    assert payload.asset == "vehicle_health_features"
    assert payload.metadata_source in ("live", "fallback")
    assert isinstance(payload.affected_models, list)
    assert len(payload.affected_models) > 0
