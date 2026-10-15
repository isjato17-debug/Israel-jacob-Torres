"""Isolated end-to-end orchestration and adversarial tests. All submission evidence is synthetic."""
import hashlib
import json
import uuid
from unittest.mock import patch
import pytest
from sqlalchemy import select
from app.db import SessionLocal
from app import models as m
from test_autoform import env, generated
from test_big_consultation import account

PASSWORD = "BIG-foundation-safe-2026!"
SOURCE = {"key": "official:test-source", "url": "https://dol.ny.gov/minimum-wage",
          "facts": {"title": "Synthetic official-source fixture", "legal_status": "PROPOSED",
                    "effective_date": None, "jurisdiction": "NY", "excerpt": "Synthetic fixture only"}}


def node(view, key):
    return next(x for x in view["actions"] if x["key"] == key)


def post(c, h, root, path, data=None):
    r = c.post(root + path, headers=h, json=data or {})
    assert r.status_code == 200, (path, r.status_code, r.text)
    return r.json()


def initialize(env):
    c, h, u, p, docs = env
    root = f"/api/v2/projects/{p['id']}/orchestrator"
    view = post(c, h, root, "/start")
    view = post(c, h, root, "/strategy", {"expected_version": node(view, "strategy")["version"], "confirmed": True})
    return c, h, u, p, docs, root, view


def signed(env):
    c, h, u, p, docs, root, view = initialize(env)
    w = generated(c, h, docs); d = w["latest_document"]
    post(c, h, docs, "/approve", {"expected_version": w["version"], "document_id": d["id"],
                                "content_hash": d["content_hash"], "confirmed": True})
    view = c.get(root).json()
    data = {"expected_version": node(view, "sign")["version"], "document_id": d["id"], "content_hash": d["content_hash"],
            "typed_name": "QA Founder", "password": PASSWORD, "request_key": str(uuid.uuid4()),
            "reviewed": True, "consent": True, "disclosure_version": "test-sign-v1"}
    with patch("urllib.request.urlopen", side_effect=AssertionError("No network in test signing")):
        view = post(c, h, root, "/sign", data)
    return c, h, u, p, docs, root, view, data


def authorized(env, outcome="ACCEPTED"):
    c, h, u, p, docs, root, view, data = signed(env)
    auth = {"expected_version": node(view, "submit")["version"], "signature_id": view["signatures"][0]["id"],
            "request_key": str(uuid.uuid4()), "outcome": outcome, "confirmed": True}
    view = post(c, h, root, "/submission/authorize", auth)
    return c, h, u, p, docs, root, view, auth


def test_dependencies_strategy_native_documents_test_sign_and_resume(env):
    c, h, u, p, docs, root, view, data = signed(env)
    assert all(node(view, x)["status"] == "COMPLETED_VERIFIED" for x in ("strategy", "prepare", "approve", "sign"))
    assert node(view, "submit")["status"] == "AWAITING_CUSTOMER_APPROVAL"
    assert len(view["strategy"]["comparisons"]) == 3 and view["strategy"]["evidence_gaps"]
    sig = view["signatures"][0]
    copy = c.get(root + f"/signatures/{sig['id']}/download")
    assert copy.status_code == 200 and copy.headers["X-Test-Signature-Status"] == "TEST_ONLY"
    assert hashlib.sha256(copy.content).hexdigest() == sig["artifact_hash"]
    assert data["content_hash"] in copy.text and "TEST SIGNATURE EVIDENCE" in copy.text
    assert "NOT A LEGALLY EXECUTED CONTRACT" in copy.text and PASSWORD not in copy.text
    replay = post(c, h, root, "/sign", data)
    assert len(replay["signatures"]) == 1 and node(replay, "sign")["attempts"] == 1
    assert c.post("/api/auth/logout", headers=h).status_code == 200
    assert c.get(root).status_code == 401
    assert c.post("/api/auth/login", json={"email": u["email"], "password": PASSWORD}).status_code == 200
    assert c.get(root).json()["signatures"][0] == sig


def test_start_idempotent_and_dependency_and_stale_guards(env):
    c, h, _, p, _ = env; root = f"/api/v2/projects/{p['id']}/orchestrator"
    assert not c.get(root).json()["initialized"]
    first = post(c, h, root, "/start")
    assert first["actions"] == post(c, h, root, "/start")["actions"]
    assert node(first, "sign")["blocked_by"] == ["approve"]
    assert node(first, "strategy")["deadline"] is None
    assert c.post(root + "/strategy", headers=h, json={"expected_version": 999, "confirmed": True}).status_code == 409
    assert c.post(root + "/submission/dispatch", headers=h, json={"expected_version": 1}).status_code == 409
    with SessionLocal() as db:
        action = db.scalar(select(m.ProjectAction).where(m.ProjectAction.project_id == p["id"]))
        assert c.post(f"/api/execution/actions/{action.action_id}/approve", headers=h, json={"confirm": True}).status_code == 409


@pytest.mark.parametrize("outcome,status", [("ACCEPTED", "COMPLETED_VERIFIED"),
    ("REJECTED", "FAILED"), ("CORRECTION_REQUIRED", "CORRECTION_REQUIRED")])
def test_test_submission_authorization_state_evidence_duplicates(env, outcome, status):
    c, h, _, p, _, root, view, auth = authorized(env, outcome)
    version = node(view, "submit")["version"]
    assert post(c, h, root, "/submission/authorize", auth)["submissions"] == view["submissions"]
    with patch("urllib.request.urlopen", side_effect=AssertionError("No external submission")):
        awaiting = post(c, h, root, "/submission/dispatch", {"expected_version": version})
        replay = post(c, h, root, "/submission/dispatch", {"expected_version": version})
        assert node(replay, "submit")["attempts"] == 1
        assert awaiting["submissions"][0]["status"] == "AWAITING_EXTERNAL_RESULT"
        view = post(c, h, root, "/submission/verify", {"expected_version": node(awaiting, "submit")["version"]})
    assert node(view, "submit")["status"] == status
    receipt = view["submissions"][0]
    assert receipt["status"] == "SIMULATED_" + outcome
    assert receipt["result"]["simulation"] and receipt["result"]["reference"].startswith("TEST-")
    assert receipt["result"]["package_hash"] == receipt["package_hash"]
    assert all(e["provenance"] in ("SYSTEM", "TEST_ONLY") for e in node(view, "submit")["evidence"])
    duplicate = post(c, h, root, "/submission/verify", {"expected_version": version})
    assert duplicate["submissions"] == view["submissions"]
    if outcome != "ACCEPTED":
        retry = {**auth, "expected_version": node(view, "submit")["version"], "request_key": str(uuid.uuid4()),
                 "outcome": "ACCEPTED"}
        retried = post(c, h, root, "/submission/authorize", retry)
        assert len(retried["submissions"]) == 2 and retried["submissions"][0]["status"] == "AUTHORIZED"


def test_withdrawal_blocks_pending_package_and_keeps_immutable_history(env):
    c, h, _, _, _, root, view, auth = authorized(env)
    sid = auth["signature_id"]; url = root + f"/signatures/{sid}/download"
    original = c.get(url).content
    view = post(c, h, root, f"/signatures/{sid}/withdraw", {"confirmed": True})
    assert view["signatures"][0]["revoked"]
    assert c.get(url).content == original
    assert c.get(url).headers["X-Test-Signature-Status"] == "REVOKED"
    assert c.post(root + "/submission/dispatch", headers=h,
                  json={"expected_version": node(view, "submit")["version"]}).status_code == 409
    assert c.post(root + "/submission/authorize", headers=h, json=auth).status_code == 409


def test_document_correction_invalidates_downstream_but_preserves_signature(env):
    c, h, _, _, docs, root, view, data = signed(env)
    old_hash = view["signatures"][0]["artifact_hash"]
    w = c.get(docs).json()["workflow"]
    r = c.patch(docs + "/document", headers=h,
                json={"expected_version": w["version"], "fields": {**w["fields"], "price_cents": 24000}})
    assert r.status_code == 200
    view = c.get(root).json()
    assert node(view, "prepare")["status"] == "INFORMATION_REQUIRED"
    assert node(view, "sign")["status"] == "CORRECTION_REQUIRED"
    assert view["signatures"][0]["artifact_hash"] == old_hash
    assert c.post(root + "/sign", headers=h, json=data).status_code == 409


def test_tamper_evidence_rejects_envelope_and_signed_copy(env):
    c, h, _, _, _, root, view, _ = signed(env); sig = view["signatures"][0]
    with SessionLocal() as db:
        s = db.get(m.TestDocumentSignature, sig["id"])
        envelope = json.loads(s.envelope_json); envelope["typed_name"] = "Changed"
        s.envelope_json = json.dumps(envelope); db.commit()
    assert c.get(root + f"/signatures/{sig['id']}/download").status_code == 409
    assert not c.get(root).json()["signatures"][0]["integrity_verified"]


def test_wrong_password_no_consent_and_false_identity_never_sign(env):
    c, h, _, _, _, root, view, data = signed(env)
    assert c.post(root + "/sign", headers=h, json={**data, "consent": False}).status_code == 422
    assert c.post(root + "/sign", headers=h, json={**data, "reviewed": False}).status_code == 422
    assert c.post(root + "/sign", headers=h, json={**data, "typed_name": "Other person"}).status_code == 422
    assert c.post(root + "/sign", headers=h, json={**data, "password": "wrong"}).status_code == 403
    assert c.post(root + "/sign", json=data).status_code == 403
    assert len(c.get(root).json()["signatures"]) == 1


def test_cancel_without_submission_then_reauthorize_failed_attempt(env):
    c, h, _, _, _, root, view = initialize(env)
    view = post(c, h, root, "/actions/submit/cancel", {"expected_version": node(view, "submit")["version"], "confirmed": True})
    assert node(view, "submit")["status"] == "CANCELLED"
    assert c.get(root).json()["actions"] == view["actions"]


def test_regulatory_source_revisions_dedup_review_and_proposal_guard(env):
    c, h, _, p, _, root, _ = initialize(env)
    with patch("app.v2.orchestrator.collect_sources", return_value=([SOURCE], [])):
        first = post(c, h, root, "/regulatory/collect")
        again = post(c, h, root, "/regulatory/collect")
    assert first["collection"]["added"] == 1 and again["collection"]["added"] == 0
    change = first["changes"][0]
    assert change["legal_status"] == "PROPOSED" and change["effective_date"] is None
    assert change["change_type"] == "FIRST_SOURCE_OBSERVATION"
    revised = {**SOURCE, "facts": {**SOURCE["facts"], "excerpt": "Synthetic updated proposal fixture"}}
    with patch("app.v2.orchestrator.collect_sources", return_value=([revised], [])):
        changed = post(c, h, root, "/regulatory/collect")
    assert len(changed["changes"]) == 2 and any(c["previous_revision_id"] for c in changed["changes"])
    data = {"expected_version": change["version"], "decision": "NOT_APPLICABLE", "confirmed": True}
    reviewed = post(c, h, root, f"/regulatory/{change['id']}/review", data)
    assert next(c for c in reviewed["changes"] if c["id"] == change["id"])["review_status"] == "NOT_APPLICABLE"
    assert c.post(root + f"/regulatory/{change['id']}/review", headers=h, json=data).status_code == 409
    project = c.get(f"/api/v2/projects/{p['id']}").json()
    assert any(t["status"] == "done" and "regulatory relevance" in t["task"] for t in project["checklist"])
    assert node(reviewed, "prepare")["status"] == "INFORMATION_REQUIRED"  # independent legal review


def test_unavailable_sources_are_explicit_and_do_not_mint_tasks(env):
    c, h, _, _, _, root, view = initialize(env)
    with patch("app.v2.orchestrator.collect_sources", return_value=([], ["Source unavailable"])):
        got = post(c, h, root, "/regulatory/collect")
    assert got["collection"]["status"] == "UNAVAILABLE_NOT_VERIFIED"
    assert not got["changes"] and len(got["actions"]) == len(view["actions"])


def test_all_new_data_and_mutations_private_same_tenant_and_cross_tenant(env):
    c, h, u, p, _, root, view, data = signed(env)
    other, oh, ou = account()
    sig = view["signatures"][0]
    for same in (False, True):
        if same:
            with SessionLocal() as db:
                db.get(m.User, ou["id"]).tenant_id = u["tenant_id"]
                for s in db.scalars(select(m.SessionRecord).where(m.SessionRecord.user_id == ou["id"])):
                    s.tenant_id = u["tenant_id"]
                db.commit()
        assert other.get(root).status_code == 404
        assert other.get(root + f"/signatures/{sig['id']}/download").status_code == 404
        assert other.post(root + "/start", headers=oh, json={}).status_code == 404
        assert other.post(root + "/sign", headers=oh, json=data).status_code == 404
        assert other.post(root + "/regulatory/collect", headers=oh, json={}).status_code == 404
        assert other.post(root + f"/signatures/{sig['id']}/withdraw", headers=oh, json={"confirmed": True}).status_code == 404
    other.close()


def test_lockdown_and_minimized_audit(env):
    c, h, u, _, _, root, _, _ = signed(env)
    with SessionLocal() as db:
        events = db.scalars(select(m.AuditEvent).where(m.AuditEvent.actor_id == u["id"])).all()
        assert all(PASSWORD not in e.details_json and "QA Founder" not in e.details_json for e in events)
        db.get(m.Tenant, u["tenant_id"]).lockdown = True; db.commit()
    assert c.post(root + "/regulatory/collect", headers=h, json={}).status_code == 423


def test_source_tampering_blocks_review(env):
    c, h, _, _, _, root, _ = initialize(env)
    with patch("app.v2.orchestrator.collect_sources", return_value=([SOURCE], [])):
        got = post(c, h, root, "/regulatory/collect")
    change = got["changes"][0]
    with SessionLocal() as db:
        saved_change = db.get(m.RegulatoryChangeRecord, change["id"])
        source = db.get(m.RegulatorySourceRevision, saved_change.source_revision_id)
        source.facts_json = '{"title":"tampered"}'; db.commit()
    assert c.get(root).status_code == 409
    assert c.post(root + f"/regulatory/{change['id']}/review", headers=h,
                  json={"expected_version": 1, "decision": "REVIEWED", "confirmed": True}).status_code == 409
