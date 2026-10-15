"""Real HTTP/API persistence against conftest's disposable DB; no external requests."""
import json
from uuid import uuid4
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app, buckets
from app.db import SessionLocal
from app.models import AIConsultation, AuditEvent, Tenant
from app.services.consultation_engine import get_consultation_provider


def account():
    c = TestClient(app)
    r = c.post("/api/auth/register", json={
        "email": f"big-{uuid4().hex}@example.com",
        "password": "BIG-foundation-safe-2026!", "tenant_name": "Disposable B.I.G.",
    })
    assert r.status_code == 200, r.text
    return c, {"X-CSRF-Token": r.json()["csrf"]}, r.json()["user"]


def prepare(c, h, language="en", detail="simple"):
    r = c.post("/api/v2/journeys", headers=h, json={
        "stage": "start", "consent": True, "language": language, "detail_mode": detail,
    })
    j = r.json()
    for field, value in [("state", "NY"), ("entity_type", "LLC"),
                         ("ownership_type", "Independent business"), ("goal", "Build a small bakery")]:
        r = c.patch(f"/api/v2/journeys/{j['id']}/answer", headers=h, json={
            "field": field, "value": value, "expected_version": j["version"],
        })
        assert r.status_code == 200, r.text
        j = r.json()
    return j


@pytest.fixture()
def env():
    buckets.clear()
    c, h, u = account()
    yield c, h, u, prepare(c, h)
    app.dependency_overrides.pop(get_consultation_provider, None)
    c.close()


def endpoint(j):
    return f"/api/v2/journeys/{j['id']}/consultation"


def send(c, h, j, version=0, **extra):
    return c.post(endpoint(j), headers=h, json={
        "consent": True, "expected_version": version, "journey_version": j["version"],
        "message": "What should I do next?", **extra,
    })


def test_simulation_persists_resumes_and_has_no_network(env):
    c, h, _, j = env
    initial = c.get(endpoint(j)).json()
    assert initial["consultation"] is None
    assert initial["availability"]["live_enabled"] is False
    assert all(x["verification"] == "REFERENCE_ONLY_NOT_STATUS_VERIFICATION" for x in initial["resources"])
    with patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")), \
         patch("httpx.AsyncClient.post", side_effect=AssertionError("Network forbidden")):
        r = send(c, h, j)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["cost"] == {"actual_cents": 0, "live_authorized": False}
    assert data["mode"] == "SIMULATION"
    assert data["turns"][0]["answer"]["classification"] == "SIMULATED_NOT_AI_GENERATED"
    assert "bakery" in data["turns"][0]["answer"]["summary"]
    assert c.get(endpoint(j)).json()["consultation"] == data


@pytest.mark.parametrize("override", [
    {"consent": False}, {"consent": None}, {"message": "    "},
    {"message": "x" * 1201}, {"expected_version": -1},
    {"expected_version": True}, {"journey_version": "5"},
    {"provider": "live"}, {"mode": "LIVE"}, {"transcript": []},
])
def test_invalid_or_client_selected_live_modes_denied(env, override):
    c, h, _, j = env
    assert send(c, h, j, **override).status_code == 422
    assert c.get(endpoint(j)).json()["consultation"] is None


def test_auth_csrf_isolation_and_lockdown(env):
    c, h, u, j = env
    outsider, oh, _ = account()
    anonymous = TestClient(app)
    assert anonymous.get(endpoint(j)).status_code == 401
    assert anonymous.post(endpoint(j), json={}).status_code in (401, 403)
    assert c.post(endpoint(j), json={
        "consent": True, "expected_version": 0, "journey_version": j["version"], "message": "A valid question",
    }).status_code == 403
    assert outsider.get(endpoint(j)).status_code == 404
    assert send(outsider, oh, j).status_code == 404
    with SessionLocal() as db:
        db.get(Tenant, u["tenant_id"]).lockdown = True
        db.commit()
    assert send(c, h, j).status_code == 423
    outsider.close()
    anonymous.close()


def test_incomplete_intake_denied(env):
    c, h, _, _ = env
    j = c.post("/api/v2/journeys", headers=h, json={"stage": "grow", "consent": True}).json()
    assert send(c, h, j).status_code == 409


def test_stale_versions_cannot_overwrite(env):
    c, h, _, j = env
    one = send(c, h, j).json()
    assert send(c, h, j).status_code == 409
    assert send(c, h, j, one["version"], journey_version=1).status_code == 409
    assert len(c.get(endpoint(j)).json()["consultation"]["turns"]) == 1


def test_context_change_is_explicit_and_can_resume_in_spanish(env):
    c, h, _, j = env
    one = send(c, h, j).json()
    revised = c.patch(f"/api/v2/journeys/{j['id']}/preferences", headers=h, json={
        "expected_version": j["version"], "language": "es", "detail_mode": "details",
    }).json()
    assert c.get(endpoint(j)).json()["consultation"]["context_stale"] is True
    assert send(c, h, j, one["version"]).status_code == 409
    r = send(c, h, revised, one["version"])
    assert r.status_code == 200, r.text
    assert r.json()["context_stale"] is False
    answer = r.json()["turns"][-1]["answer"]
    assert "Simulación" in answer["summary"]
    assert "NY" in answer["roadmap"][0]["explanation"]


def test_turn_limit_and_audit_minimization(env):
    c, h, u, j = env
    version = 0
    for _ in range(8):
        r = send(c, h, j, version, message="A private business question")
        assert r.status_code == 200, r.text
        version = r.json()["version"]
    assert send(c, h, j, version).status_code == 429
    with SessionLocal() as db:
        events = db.scalars(select(AuditEvent).where(
            AuditEvent.tenant_id == u["tenant_id"], AuditEvent.action == "consultation_simulated",
        )).all()
        assert len(events) == 8
        assert all("private business" not in x.details_json and "bakery" not in x.details_json for x in events)


@pytest.mark.parametrize("fault", ["malformed", "timeout", "unknown_source"])
def test_provider_failure_preserves_progress(env, fault):
    c, h, _, j = env
    saved = send(c, h, j).json()
    class Broken:
        def recommend(self, **kwargs):
            if fault == "timeout":
                raise TimeoutError("private driver details must not leak")
            if fault == "unknown_source":
                result = saved["turns"][0]["answer"].copy()
                result["source_ids"] = ["malicious-source"]
                return result
            return {"summary": "invalid", "official_status": "APPROVED"}
    app.dependency_overrides[get_consultation_provider] = lambda: Broken()
    r = send(c, h, j, saved["version"])
    assert r.status_code == 503
    assert "private driver" not in r.text
    assert c.get(endpoint(j)).json()["consultation"] == saved


def test_same_tenant_different_user_cannot_access(env):
    c, h, u, j = env
    other, oh, ou = account()
    from app.models import User, SessionRecord
    with SessionLocal() as db:
        db.get(User, ou["id"]).tenant_id = u["tenant_id"]
        for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == ou["id"])):
            session.tenant_id = u["tenant_id"]
        db.commit()
    assert other.get(endpoint(j)).status_code == 404
    assert send(other, oh, j).status_code == 404
    other.close()


def test_all_six_languages_save_resume_and_localize_simulation(env):
    c, h, _, j = env
    markers = {"en": "No-AI", "es": "Simulación", "zh": "模拟",
               "ar": "محاكاة", "hi": "अनुकरण", "sw": "Uigaji"}
    version = 0
    for locale, marker in markers.items():
        response = c.patch(f"/api/v2/journeys/{j['id']}/preferences", headers=h, json={
            "expected_version": j["version"], "language": locale, "detail_mode": "simple",
        })
        assert response.status_code == 200, response.text
        j = response.json()
        result = send(c, h, j, version)
        assert result.status_code == 200, result.text
        data = result.json()
        version = data["version"]
        assert data["language"] == locale
        assert marker in data["turns"][-1]["answer"]["summary"]
        assert c.get("/api/v2/journeys").json()["journeys"][0]["language"] == locale
        resumed = c.get(endpoint(j)).json()
        assert resumed["consultation"]["language"] == locale
        assert any(r["id"] == "sba-local" for r in resumed["resources"])
        if locale != "en":
            assert next(r["title"] for r in resumed["resources"] if r["id"] == "sba-local") != "SBA — local assistance, SBDC and SCORE mentoring"
    assert c.patch(f"/api/v2/journeys/{j['id']}/preferences", headers=h, json={
        "expected_version": j["version"], "language": "unknown", "detail_mode": "simple",
    }).status_code == 422
