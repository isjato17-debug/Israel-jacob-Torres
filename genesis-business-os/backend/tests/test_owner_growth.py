"""Private operator planning tests; conftest forces a disposable test database."""
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.main import app, buckets
from app.models import AuditEvent, User

URL = "/api/v2/operator/campaigns"
DRAFT = {
    "title": "Original founder guide", "objective": "Help new founders understand the first safe step",
    "audience": "First-time entrepreneurs", "channel": "website",
    "content": "Write an original guide with clearly stated limitations and no invented testimonials.",
    "planned_budget_cents": 12550,
}


def account():
    client = TestClient(app)
    response = client.post("/api/auth/register", json={
        "tenant_name": "Operator QA", "email": f"operator-{uuid4().hex}@example.com",
        "password": "OperatorQA!2026-strong",
    })
    assert response.status_code == 200, response.text
    return client, {"X-CSRF-Token": response.json()["csrf"]}, response.json()["user"]


@pytest.fixture()
def owner(monkeypatch):
    buckets.clear()
    client, headers, user = account()
    monkeypatch.setattr(settings, "platform_owner_user_ids", user["id"])
    yield client, headers, user
    client.close()


def create(client, headers, **values):
    result = client.post(URL, headers=headers, json={**DRAFT, **values})
    assert result.status_code == 200, result.text
    return result.json()


def review(client, headers, campaign, action, confirm=False):
    return client.post(f"{URL}/{campaign['id']}/review", headers=headers, json={
        "action": action, "expected_version": campaign["version"], "confirm": confirm,
    })


def approve(client, headers):
    campaign = create(client, headers)
    campaign = review(client, headers, campaign, "request_review").json()
    result = review(client, headers, campaign, "approve", True)
    assert result.status_code == 200, result.text
    return result.json()


def test_default_deny_and_customer_owner_cannot_self_elevate(monkeypatch):
    buckets.clear()
    monkeypatch.setattr(settings, "platform_owner_user_ids", "")
    client, headers, user = account()
    access = client.get("/api/v2/operator/access").json()
    assert access["owner_access"] is False
    assert access["account_id"] == user["id"]
    assert access["configuration_required"] is True
    assert client.get(URL).status_code == 403
    assert client.post(URL, headers={**headers, "X-Platform-Owner": user["id"]}, json=DRAFT).status_code == 403
    assert TestClient(app).get(URL).status_code == 401


def test_allowlist_and_owner_role_both_required(owner):
    client, _, user = owner
    assert client.get("/api/v2/operator/access").json()["owner_access"] is True
    with SessionLocal() as db:
        db.get(User, user["id"]).role = "member"
        db.commit()
    assert client.get("/api/v2/operator/access").json()["owner_access"] is False
    assert client.get(URL).status_code == 403


def test_create_list_and_real_aggregate(owner):
    client, headers, _ = owner
    campaign = create(client, headers)
    assert campaign["status"] == "DRAFT"
    assert campaign["version"] == 1
    assert campaign["publishing_enabled"] is False
    assert campaign["spending_authorized"] is False
    assert campaign["verified_performance"] is None
    result = client.get(URL).json()
    assert result["overview"]["campaign_count"] == 1
    assert result["overview"]["planned_budget_cents"] == 12550
    assert result["overview"]["verified_performance"] is None
    assert result["campaigns"][0]["content"] == DRAFT["content"]
    assert result["capabilities"]["publishing"] is False


@pytest.mark.parametrize("budget", [-1, 1.25, True, 100_000_001])
def test_invalid_budgets_rejected(owner, budget):
    client, headers, _ = owner
    assert client.post(URL, headers=headers, json={**DRAFT, "planned_budget_cents": budget}).status_code == 422


def test_csrf_and_server_owned_fields(owner):
    client, headers, user = owner
    assert client.post(URL, json=DRAFT).status_code == 403
    for extra in [{"status": "APPROVED"}, {"creator_id": user["id"]}, {"spending_authorized": True}]:
        assert client.post(URL, headers=headers, json={**DRAFT, **extra}).status_code == 422


def test_review_requires_content_and_explicit_confirmation(owner):
    client, headers, _ = owner
    empty = create(client, headers, content="")
    assert review(client, headers, empty, "request_review").status_code == 422
    campaign = create(client, headers)
    assert review(client, headers, campaign, "approve", True).status_code == 409
    campaign = review(client, headers, campaign, "request_review").json()
    assert review(client, headers, campaign, "approve").status_code == 422
    approved = review(client, headers, campaign, "approve", True).json()
    assert approved["status"] == "APPROVED"
    assert approved["approved_at"].endswith("+00:00")
    assert approved["spending_authorized"] is False
    assert approved["publishing_enabled"] is False


def test_edit_invalidates_previous_approval_and_stale_edits_fail(owner):
    client, headers, _ = owner
    campaign = approve(client, headers)
    body = {**DRAFT, "title": "Revised original guide", "expected_version": campaign["version"]}
    changed = client.put(f"{URL}/{campaign['id']}", headers=headers, json=body)
    assert changed.status_code == 200
    assert changed.json()["status"] == "DRAFT"
    assert changed.json()["approved_at"] is None
    assert client.put(f"{URL}/{campaign['id']}", headers=headers, json=body).status_code == 409
    assert client.get(URL).json()["campaigns"][0]["title"] == "Revised original guide"


def test_archive_is_reversible_and_excludes_budget_without_deleting(owner):
    client, headers, _ = owner
    campaign = create(client, headers)
    archived = review(client, headers, campaign, "archive").json()
    assert archived["status"] == "ARCHIVED"
    assert client.get(URL).json()["overview"]["planned_budget_cents"] == 0
    assert client.get(URL).json()["overview"]["campaign_count"] == 1
    assert client.put(f"{URL}/{campaign['id']}", headers=headers, json={
        **DRAFT, "expected_version": archived["version"],
    }).status_code == 409
    assert review(client, headers, archived, "reopen").json()["status"] == "DRAFT"
    assert client.get(URL).json()["overview"]["planned_budget_cents"] == 12550


def test_cross_tenant_access_denied_even_to_another_allowlisted_owner(owner, monkeypatch):
    client, headers, user = owner
    campaign = create(client, headers)
    other, other_headers, other_user = account()
    monkeypatch.setattr(settings, "platform_owner_user_ids", f"{user['id']},{other_user['id']}")
    assert other.get(URL).json()["campaigns"] == []
    assert review(other, other_headers, campaign, "archive").status_code == 404
    assert other.put(f"{URL}/{campaign['id']}", headers=other_headers, json={
        **DRAFT, "expected_version": 1,
    }).status_code == 404


def test_lockdown_blocks_creation_edit_and_review(owner):
    client, headers, _ = owner
    campaign = create(client, headers)
    assert client.post("/api/security/lockdown", headers=headers, json={"enabled": True}).status_code == 200
    assert client.post(URL, headers=headers, json=DRAFT).status_code == 423
    assert client.put(f"{URL}/{campaign['id']}", headers=headers, json={**DRAFT, "expected_version": 1}).status_code == 423
    assert review(client, headers, campaign, "request_review").status_code == 423
    assert client.get(URL).status_code == 200


def test_no_publishing_or_spending_action_and_no_content_in_audit(owner):
    client, headers, user = owner
    campaign = create(client, headers)
    assert review(client, headers, campaign, "publish").status_code == 422
    assert client.post(f"{URL}/{campaign['id']}/publish", headers=headers, json={}).status_code == 404
    with SessionLocal() as db:
        rows = db.scalars(select(AuditEvent).where(AuditEvent.actor_id == user["id"])).all()
        details = json.dumps([json.loads(row.details_json) for row in rows])
        assert any(row.action == "growth_created" for row in rows)
        assert DRAFT["content"] not in details
