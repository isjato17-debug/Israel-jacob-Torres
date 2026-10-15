import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from app.services import provider_status
from app.services.execution_hub import CATALOG, connection_status
from app.services.ai_provider import AIProvider, LiveUsageNotAuthorized
from app.services.automation_foundation import (
    AGENTS, WorkflowState, transition, RevenueEvidence, planned_ai_budget, enforce_agent_permission,
)
from app.services.readiness import check_readiness
from app.main import app, buckets
from fastapi.testclient import TestClient


def test_configuration_is_never_verification(monkeypatch):
    provider_status._records.clear()
    point = CATALOG["email_send"]
    for key in point.credential_env:
        monkeypatch.delenv(key, raising=False)
    assert connection_status(point)["state"] == "NOT_CONFIGURED"
    for key in point.credential_env:
        monkeypatch.setenv(key, "offline-fixture")
    assert connection_status(point)["state"] == "CONFIGURED"
    with pytest.raises(ValueError):
        provider_status.record_verification(point.key, point.credential_env, "VERIFIED_CONNECTED")
    for state in ("VERIFICATION_PENDING", "ERROR", "UNAVAILABLE"):
        provider_status.record_verification(point.key, point.credential_env, state)
        assert connection_status(point)["state"] == state
    provider_status.record_verification(point.key, point.credential_env, "VERIFIED_CONNECTED", successful=True)
    assert connection_status(point)["verified"] is True
    monkeypatch.setenv(point.credential_env[0], "rotated-offline-fixture")
    assert connection_status(point)["state"] == "CONFIGURED"
    provider_status._records.clear()


def test_verification_expires(monkeypatch):
    keys = ["GENESIS_TEST_PROVIDER_ONLY"]
    monkeypatch.setenv(keys[0], "offline")
    provider_status.record_verification("qa", keys, "VERIFIED_CONNECTED", successful=True)
    with patch.object(provider_status.time, "monotonic", return_value=provider_status.time.monotonic() + 301):
        assert provider_status.status("qa", keys)["state"] == "CONFIGURED"
    provider_status._records.clear()


def test_ai_cannot_activate_from_environment(monkeypatch):
    for key, value in [("GENESIS_AI_PROVIDER", "openai"), ("GENESIS_AI_API_KEY", "fixture-not-a-key"),
                       ("GENESIS_AI_BASE_URL", "https://invalid.example.com"), ("GENESIS_AI_MODEL", "fixture")]:
        monkeypatch.setenv(key, value)
    ai = AIProvider()
    assert ai.enabled() is False
    for operation in (ai.structured_analysis, ai._authorized_transport):
        with pytest.raises(LiveUsageNotAuthorized):
            operation("private", {})
    assert ai.build_request("instruction", {"goal": "fixture"})["max_tokens"] == 1200


def test_revenue_budget_uses_only_verified_net_and_authorizes_zero():
    evidence = RevenueEvidence(10000, 1000, 300, 700, verified=True)
    budget = planned_ai_budget(evidence)
    assert budget["eligible_cents"] == 8000
    assert budget["planning_limit_cents"] == 400
    assert budget["spend_authorized_cents"] == budget["per_agent_live_limit_cents"] == 0
    assert planned_ai_budget(RevenueEvidence(999999, 0, 0, 0))["eligible_cents"] == 0
    assert planned_ai_budget(RevenueEvidence(100, 200, 0, 0, True))["eligible_cents"] == 0
    for amount in (501, -1, 5.0, True):
        with pytest.raises(ValueError):
            planned_ai_budget(evidence, amount)


def test_agent_plans_are_not_execution_and_require_oversight():
    assert len(AGENTS) == 9
    for key, policy in AGENTS.items():
        assert policy.status == "PLANNED_NOT_ACTIVE" and not policy.external_actions
        enforce_agent_permission(key, "prepare_draft")
        with pytest.raises(PermissionError):
            enforce_agent_permission(key, "send_email")
        with pytest.raises(PermissionError):
            enforce_agent_permission(key, "prepare_draft", 1)
    s = transition(WorkflowState.DRAFT, "request_review")
    with pytest.raises(PermissionError):
        transition(s, "owner_approve_plan")
    assert transition(s, "owner_approve_plan", owner_approved=True) == WorkflowState.APPROVED_PLAN
    assert transition(WorkflowState.BLOCKED, "retry") == WorkflowState.DRAFT
    with pytest.raises(ValueError):
        transition(WorkflowState.APPROVED_PLAN, "external_execute")


def test_readiness_has_redacted_failure_and_health_is_independent():
    buckets.clear()
    c = TestClient(app)
    assert c.get("/healthz").status_code == 200
    assert c.get("/api/readyz").json()["status"] == "ready"
    with patch("app.main.check_readiness", return_value={"database": False, "schema": False}):
        result = c.get("/api/readyz")
        assert result.status_code == 503 and "password" not in result.text
        assert c.get("/healthz").status_code == 200
    empty = create_engine("sqlite://")
    assert check_readiness(empty, "development") == {"database": True, "schema": False}
    assert check_readiness(empty, "production") == {"database": True, "schema": False}
    empty.dispose()
