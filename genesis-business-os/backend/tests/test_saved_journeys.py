"""Consent, progress, isolation and concurrency on the disposable pytest database."""
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app, buckets
from app.db import SessionLocal
from app.models import AuditEvent, Business, SessionRecord, User


def account():
    client = TestClient(app)
    result = client.post("/api/auth/register", json={
        "tenant_name": "Journey QA",
        "email": f"journey-{uuid4().hex}@example.com",
        "password": "JourneyQA!2026-strong",
    })
    assert result.status_code == 200, result.text
    return client, {"X-CSRF-Token": result.json()["csrf"]}, result.json()["user"]


@pytest.fixture()
def signed_in():
    buckets.clear()
    client, headers, user = account()
    yield client, headers, user
    client.close()


def start(client, headers, stage="start", **extra):
    result = client.post("/api/v2/journeys", headers=headers, json={
        "stage": stage, "consent": True, **extra,
    })
    assert result.status_code == 200, result.text
    return result.json()


def answer(client, headers, journey, field, value):
    return client.patch(f"/api/v2/journeys/{journey['id']}/answer", headers=headers, json={
        "field": field, "value": value, "expected_version": journey["version"],
    })


def prepared(client, headers):
    journey = start(client, headers)
    for field, value in [
        ("state", "NY"), ("entity_type", "LLC"),
        ("ownership_type", "Independent business"),
        ("goal", "Build a weekend bakery with a reviewed launch plan"),
    ]:
        response = answer(client, headers, journey, field, value)
        assert response.status_code == 200, response.text
        journey = response.json()
    return journey


def test_authentication_and_csrf_required(signed_in):
    client, headers, _ = signed_in
    anonymous = TestClient(app)
    assert anonymous.get("/api/v2/journeys").status_code == 401
    assert client.post("/api/v2/journeys", json={"stage": "start", "consent": True}).status_code == 403
    journey = start(client, headers)
    assert client.patch(f"/api/v2/journeys/{journey['id']}/answer", json={
        "field": "state", "value": "NY", "expected_version": 1,
    }).status_code == 403


def test_explicit_consent_required(signed_in):
    client, headers, _ = signed_in
    for consent in [False, None]:
        body = {"stage": "start"}
        if consent is not None:
            body["consent"] = consent
        assert client.post("/api/v2/journeys", headers=headers, json=body).status_code == 422
    assert client.get("/api/v2/journeys").json()["journeys"] == []


def test_resume_and_no_duplicate_workspace(signed_in):
    client, headers, user = signed_in
    journey = start(client, headers)
    assert journey["next_question"] == "state"
    saved = answer(client, headers, journey, "state", "NY").json()
    resumed = client.get("/api/v2/journeys").json()["journeys"][0]
    assert resumed["id"] == journey["id"]
    assert resumed["answers"] == {"state": "NY"}
    assert resumed["next_question"] == "entity_type"
    assert resumed["version"] == saved["version"] == 2
    assert resumed["updated_at"].endswith("+00:00")
    assert start(client, headers)["id"] == journey["id"]
    with SessionLocal() as db:
        assert len(db.scalars(select(Business).where(Business.tenant_id == user["tenant_id"])).all()) == 1


def test_draft_progress_is_not_service_completion(signed_in):
    client, headers, _ = signed_in
    journey = prepared(client, headers)
    assert journey["status"] == "PREPARED"
    assert journey["answered_count"] == journey["question_count"] == 4
    assert journey["plan"]["persisted"] is True
    assert "does not save" not in journey["plan"]["notice"]
    assert journey["data_classification"] == "USER_PROVIDED_NOT_VERIFIED"
    assert journey["cost"] == {"amount_cents": None, "status": "NOT_QUOTED", "charges_authorized": False}
    assert all(step["workflow_status"] == "NOT_STARTED" and step["completed"] is False
               and step["price_cents"] is None for step in journey["plan"]["steps"])
    denied = client.patch(f"/api/v2/journeys/{journey['id']}/answer", headers=headers, json={
        "field": "status", "value": "COMPLETED", "expected_version": journey["version"],
    })
    assert denied.status_code == 422


def test_reuses_only_authorized_answers_between_stages(signed_in):
    client, headers, _ = signed_in
    original = prepared(client, headers)
    growth = start(client, headers, stage="grow", language="es", detail_mode="details")
    assert growth["id"] != original["id"]
    assert growth["business_id"] == original["business_id"]
    assert growth["answers"] == {key: value for key, value in original["answers"].items() if key != "goal"}
    assert growth["next_question"] == "goal"
    assert growth["language"] == "es"
    assert growth["detail_mode"] == "details"
    assert growth["plan"] is None
    assert growth["data_classification"] == "USER_PROVIDED_NOT_VERIFIED"


def test_stale_writes_rejected_without_losing_progress(signed_in):
    client, headers, _ = signed_in
    journey = start(client, headers)
    saved = answer(client, headers, journey, "state", "NY").json()
    assert answer(client, headers, journey, "state", "CA").status_code == 409
    latest = client.get("/api/v2/journeys").json()["journeys"][0]
    assert latest["answers"]["state"] == "NY"
    assert latest["version"] == saved["version"]


def test_validation_does_not_skip_questions(signed_in):
    client, headers, _ = signed_in
    journey = start(client, headers)
    assert answer(client, headers, journey, "goal", "A valid goal before the state").status_code == 422
    assert answer(client, headers, journey, "state", "ZZ").status_code == 422
    assert answer(client, headers, journey, "state", "  ").status_code == 422
    assert client.get("/api/v2/journeys").json()["journeys"][0]["version"] == 1


def test_customer_and_tenant_isolation(signed_in):
    client, headers, user = signed_in
    journey = start(client, headers)
    other, other_headers, other_user = account()
    assert other.get("/api/v2/journeys").json()["journeys"] == []
    assert answer(other, other_headers, journey, "state", "CA").status_code == 404
    # Even another member of the SAME tenant cannot access this user's consented intake.
    with SessionLocal() as db:
        db.get(User, other_user["id"]).tenant_id = user["tenant_id"]
        for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == other_user["id"])):
            session.tenant_id = user["tenant_id"]
        db.commit()
    assert other.get("/api/v2/journeys").json()["journeys"] == []
    assert answer(other, other_headers, journey, "state", "CA").status_code == 404
    assert start(other, other_headers)["answers"] == {}


def test_preferences_saved_with_version_protection(signed_in):
    client, headers, _ = signed_in
    journey = start(client, headers)
    url = f"/api/v2/journeys/{journey['id']}/preferences"
    payload = {"language": "es", "detail_mode": "details", "expected_version": 1}
    result = client.patch(url, headers=headers, json=payload)
    assert result.status_code == 200
    assert result.json()["language"] == "es"
    assert result.json()["detail_mode"] == "details"
    assert result.json()["version"] == 2
    assert client.patch(url, headers=headers, json=payload).status_code == 409


def test_lockdown_blocks_journey_writes(signed_in):
    client, headers, _ = signed_in
    journey = start(client, headers)
    assert client.post("/api/security/lockdown", headers=headers, json={"enabled": True}).status_code == 200
    assert answer(client, headers, journey, "state", "NY").status_code == 423
    assert client.post("/api/v2/journeys", headers=headers, json={"stage": "grow", "consent": True}).status_code == 423
    assert client.get("/api/v2/journeys").status_code == 200


def test_answers_can_be_corrected_and_are_not_copied_into_audit_logs(signed_in):
    client, headers, user = signed_in
    journey = prepared(client, headers)
    changed = answer(client, headers, journey, "state", "CA").json()
    assert changed["plan"]["state_name"] == "California"
    assert changed["status"] == "PREPARED"
    with SessionLocal() as db:
        logs = db.scalars(select(AuditEvent).where(AuditEvent.actor_id == user["id"])).all()
        assert any(row.action == "journey_answer_saved" for row in logs)
        details = json.dumps([json.loads(row.details_json) for row in logs])
        assert "weekend bakery" not in details
