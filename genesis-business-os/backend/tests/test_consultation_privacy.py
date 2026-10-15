"""Privacy decisions must not erase intake or silently restore withdrawn transcripts."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app, buckets
from app.db import SessionLocal
from app.models import AIConsultation, AuditEvent, OnboardingJourney, Tenant
from test_big_consultation import account, prepare, endpoint, send
from app.services.consultation_engine import get_consultation_provider


@pytest.fixture()
def env():
    buckets.clear()
    c, h, u = account()
    j = prepare(c, h)
    yield c, h, u, j
    c.close()


def decide(c, h, j, action, **extra):
    state = c.get(endpoint(j)).json()
    return c.post(endpoint(j) + "/privacy", headers=h, json={
        "action": action, "confirmed": True, "expected_version": state["privacy"]["version"],
        "consultation_version": (state["consultation"] or {}).get("version", 0), **extra,
    })


def test_withdraw_delete_reconsent_and_no_stale_resurrection(env):
    c, h, _, j = env
    one = send(c, h, j).json()
    assert decide(c, h, j, "revoke").status_code == 200
    state = c.get(endpoint(j)).json()
    assert state["privacy"]["status"] == "REVOKED" and state["consultation"]["turns"]
    assert send(c, h, j, state["consultation"]["version"], privacy_version=1).status_code == 409
    assert decide(c, h, j, "delete").status_code == 200
    state = c.get(endpoint(j)).json()
    assert state["privacy"]["status"] == "DELETED"
    assert state["consultation"]["turns"] == []
    with SessionLocal() as db:
        item = db.get(AIConsultation, one["id"])
        assert item and item.turns_json == "[]"
        journey = db.get(OnboardingJourney, j["id"])
        assert json.loads(journey.answers_json)["goal"] == "Build a small bakery"
    assert send(c, h, j, state["consultation"]["version"], privacy_version=2).status_code == 409
    assert decide(c, h, j, "grant").status_code == 200
    new = c.get(endpoint(j)).json()
    # An old request, even with an explicit consent checkbox, cannot bypass re-consent versioning.
    assert send(c, h, j, one["version"]).status_code == 409
    assert send(c, h, j, new["consultation"]["version"]).status_code == 409
    r = send(c, h, j, new["consultation"]["version"], privacy_version=new["privacy"]["version"])
    assert r.status_code == 200 and len(r.json()["turns"]) == 1
    with SessionLocal() as db:
        events = db.scalars(select(AuditEvent).where(AuditEvent.resource_type == "consultation_privacy")).all()
        assert events and all("bakery" not in e.details_json and "question" not in e.details_json for e in events)


@pytest.mark.parametrize("action", ["revoke", "delete", "grant"])
def test_auth_csrf_confirmation_stale_and_lockdown(env, action):
    c, h, u, j = env
    outsider, oh, _ = account()
    url = endpoint(j) + "/privacy"
    body = {"action": action, "expected_version": 0, "consultation_version": 0, "confirmed": True}
    assert TestClient(app).post(url, json=body).status_code == 401
    assert c.post(url, json=body).status_code == 403
    assert outsider.post(url, headers=oh, json=body).status_code == 404
    assert c.post(url, headers=h, json={**body, "confirmed": False}).status_code == 422
    assert c.post(url, headers=h, json={**body, "expected_version": 1}).status_code == 409
    assert c.post(url, headers=h, json=body).status_code == 200
    assert c.post(url, headers=h, json=body).status_code == 409
    with SessionLocal() as db:
        db.get(Tenant, u["tenant_id"]).lockdown = True; db.commit()
    assert decide(c, h, j, "grant").status_code == 423
    outsider.close()


def test_delete_before_first_consultation_blocks_old_zero_version_request(env):
    c, h, _, j = env
    assert decide(c, h, j, "delete").status_code == 200
    assert c.get(endpoint(j)).json()["consultation"] is None
    assert send(c, h, j).status_code == 409


def test_inflight_reply_cannot_restore_deleted_content(env):
    c, h, _, j = env
    one = send(c, h, j).json()
    original = get_consultation_provider()

    class DelayedProvider:
        def recommend(self, **kwargs):
            assert decide(c, h, j, "delete").status_code == 200
            return original.recommend(**kwargs)

    app.dependency_overrides[get_consultation_provider] = lambda: DelayedProvider()
    try:
        assert send(c, h, j, one["version"]).status_code == 409
    finally:
        app.dependency_overrides.pop(get_consultation_provider, None)
    state = c.get(endpoint(j)).json()
    assert state["privacy"]["status"] == "DELETED"
    assert state["consultation"]["turns"] == []
