"""Private, real document lifecycle; no external actions or original customer data."""
import hashlib
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app, buckets
from app.db import SessionLocal
from app.models import (AuditEvent, BusinessPassport, DocumentWorkflow, GeneratedDocument,
                        DocumentApproval, Tenant, User, FounderProfile, SessionRecord)
from app.security import hash_password
from test_big_consultation import account
from test_idea_vault import develop

PASS = {"business_name": "Bright Start Cleaning", "representative_name": "QA Founder",
        "business_email": "cleaning@example.com", "municipality": "Albany"}
DETAILS = {"client_name": "QA Client", "service_address": "100 Example Street, Albany, NY",
           "service_scope": "Clean kitchen, bathrooms and floors. Excludes hazardous waste and mold remediation.",
           "frequency": "Every two weeks, Tuesdays at 10am", "price_cents": 22025,
           "payment_terms": "Payment due after each visit by a separately agreed method.",
           "start_date": "2026-11-10", "cancellation_terms": "Either party may cancel with 48 hours notice.",
           "supplies_terms": "Provider supplies routine products; client provides safe access and discloses hazards."}


@pytest.fixture()
def env():
    buckets.clear()
    c, h, u = account()
    _, p = develop(c, h)
    yield c, h, u, p, f"/api/v2/projects/{p['id']}/execution"
    c.close()


def started(c, h, root):
    r = c.put(root + "/passport", headers=h, json={"expected_version": 0, "consent": True, "fields": PASS})
    assert r.status_code == 200, r.text
    r = c.post(root + "/documents", headers=h, json={"template_key": "cleaning_service_agreement"})
    assert r.status_code == 200, r.text
    return r.json()["workflow"]


def generated(c, h, root):
    w = started(c, h, root)
    r = c.patch(root + "/document", headers=h,
                json={"expected_version": w["version"], "fields": {**w["fields"], **DETAILS}})
    assert r.status_code == 200, r.text
    r = c.post(root + "/generate", headers=h, json={"expected_version": r.json()["workflow"]["version"]})
    assert r.status_code == 200, r.text
    return r.json()["workflow"]


def test_connected_document_complete_correct_approve_resume(env):
    c, h, u, p, root = env
    before = c.get(f"/api/v2/projects/{p['id']}").json()
    ctx = c.get(root).json()
    assert ctx["assistant"]["live_ai_connected"] is False
    assert ctx["assistant"]["classification"] == "DETERMINISTIC_NOT_AI_GENERATED"
    assert ctx["assistant"]["board"]["agents"]["CFO"]
    assert ctx["assistant"]["founder_dna"]["assessment"] is None
    with patch("urllib.request.urlopen", side_effect=AssertionError("No network for native execution")):
        w = generated(c, h, root)
    d = w["latest_document"]
    url = root + f"/documents/{d['id']}/download"
    download = c.get(url)
    assert download.status_code == 200
    assert hashlib.sha256(download.content).hexdigest() == d["content_hash"]
    assert "attachment;" in download.headers["Content-Disposition"]
    assert "no-store" in download.headers["Cache-Control"]
    assert "QA Client" in download.text and "$220.25" in download.text
    assert "Provider signature" in download.text and "Signature: ____" in download.text
    # A correction retains the old generated record but invalidates readiness.
    r = c.patch(root + "/document", headers=h,
                json={"expected_version": w["version"], "fields": {**w["fields"], "price_cents": 22575}})
    assert r.status_code == 200
    assert r.json()["workflow"]["status"] == "DRAFT"
    r = c.post(root + "/generate", headers=h, json={"expected_version": r.json()["workflow"]["version"]})
    w = r.json()["workflow"]; d = w["latest_document"]
    assert len(w["documents"]) == 2 and d["revision"] == 2
    assert "$225.75" in c.get(root + f"/documents/{d['id']}/download").text
    r = c.post(root + "/approve", headers=h, json={"expected_version": w["version"],
               "document_id": d["id"], "content_hash": d["content_hash"], "confirmed": True})
    assert r.status_code == 200, r.text
    assert r.json()["workflow"]["status"] == "READY_FOR_SIGNATURE"
    assert "signature process" in r.json()["assistant"]["next_action"]
    after = c.get(f"/api/v2/projects/{p['id']}").json()
    assert after["stage"] == "SIGNATURE_READY"
    assert after["plan"] == before["plan"] and after["budget_cents"] == 300000
    assert any(t["status"] == "done" and "Cleaning Service Agreement" in t["task"] for t in after["checklist"])
    assert c.post("/api/auth/logout", headers=h).status_code == 200
    assert c.get(url).status_code == 401
    r = c.post("/api/auth/login", json={"email": u["email"], "password": "BIG-foundation-safe-2026!"})
    assert r.status_code == 200
    resumed = c.get(root).json()
    assert resumed["workflow"]["latest_document"]["id"] == d["id"]
    assert resumed["workflow"]["latest_document"]["approval"]["purpose"] == "SIGNATURE_PREPARATION_ONLY"
    # Original revision remains immutable and accessible to its owner only.
    assert hashlib.sha256(c.get(url).content).hexdigest() == w["documents"][1]["content_hash"]


def test_passport_reuse_missing_draft_and_required_information(env):
    c, h, _, _, root = env
    w = started(c, h, root)
    assert all(w["fields"][k] == v for k, v in PASS.items())
    assert "client_name" in w["missing"]
    assert c.post(root + "/generate", headers=h, json={"expected_version": w["version"]}).status_code == 422
    r = c.patch(root + "/document", headers=h,
                json={"expected_version": w["version"], "fields": {**w["fields"], "client_name": "Saved partial"}})
    assert r.status_code == 200 and r.json()["workflow"]["fields"]["client_name"] == "Saved partial"


def test_other_tenant_and_same_tenant_customer_denied(env):
    c, h, u, p, root = env
    w = generated(c, h, root); d = w["latest_document"]
    other, oh, ou = account()
    for same_tenant in (False, True):
        if same_tenant:
            with SessionLocal() as db:
                db.get(User, ou["id"]).tenant_id = u["tenant_id"]
                for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == ou["id"])):
                    session.tenant_id = u["tenant_id"]
                db.commit()
        assert other.get(root).status_code == 404
        assert other.get(root + f"/documents/{d['id']}/download").status_code == 404
        assert other.put(root + "/passport", headers=oh, json={"expected_version": 0, "consent": True, "fields": PASS}).status_code == 404
        assert other.post(root + "/generate", headers=oh, json={"expected_version": w["version"]}).status_code == 404
        assert other.post(root + "/approve", headers=oh, json={"expected_version": w["version"],
            "document_id": d["id"], "content_hash": d["content_hash"], "confirmed": True}).status_code == 404
    other.close()


def test_consent_csrf_strict_fields_and_lockdown(env):
    c, h, u, _, root = env
    payload = {"expected_version": 0, "consent": True, "fields": PASS}
    assert c.put(root + "/passport", json=payload).status_code == 403
    assert c.put(root + "/passport", headers=h, json={**payload, "consent": False}).status_code == 422
    assert c.put(root + "/passport", headers=h, json={**payload, "user_id": "spoof"}).status_code == 422
    with SessionLocal() as db:
        db.get(Tenant, u["tenant_id"]).lockdown = True; db.commit()
    assert c.put(root + "/passport", headers=h, json=payload).status_code == 423


def test_versions_exact_approval_and_post_approval_corrections(env):
    c, h, _, _, root = env
    w = generated(c, h, root); d = w["latest_document"]
    approval = {"expected_version": w["version"], "document_id": d["id"],
                "content_hash": d["content_hash"], "confirmed": True}
    assert c.post(root + "/approve", headers=h, json={**approval, "confirmed": False}).status_code == 422
    assert c.post(root + "/approve", headers=h, json={**approval, "content_hash": "0" * 64}).status_code == 409
    assert c.post(root + "/approve", headers=h, json={**approval, "expected_version": w["version"] - 1}).status_code == 409
    r = c.post(root + "/approve", headers=h, json=approval)
    assert r.status_code == 200
    assert c.post(root + "/approve", headers=h, json=approval).status_code == 409
    w = r.json()["workflow"]
    corrected = {**w["fields"], "frequency": "Weekly, starting after both parties sign"}
    r = c.patch(root + "/document", headers=h, json={"expected_version": w["version"], "fields": corrected})
    assert r.json()["workflow"]["status"] == "DRAFT"
    assert r.json()["workflow"]["latest_document"]["approval"]  # Immutable historical approval.
    assert c.post(root + "/approve", headers=h,
                  json={**approval, "expected_version": r.json()["workflow"]["version"]}).status_code == 409


@pytest.mark.parametrize("extra", [{"price_cents": True}, {"price_cents": 12.5},
                                    {"price_cents": -1}, {"start_date": "2026-02-30"},
                                    {"client_name": "x" * 161}, {"service_scope": "bad\x00text"}])
def test_field_validation(env, extra):
    c, h, _, _, root = env
    w = started(c, h, root)
    assert c.patch(root + "/document", headers=h,
        json={"expected_version": w["version"], "fields": {**w["fields"], **DETAILS, **extra}}).status_code == 422


def test_download_escaping_integrity_and_minimal_audit(env):
    c, h, u, p, root = env
    w = generated(c, h, root)
    r = c.patch(root + "/document", headers=h, json={"expected_version": w["version"],
        "fields": {**w["fields"], "client_name": "<script>alert(1)</script>"}})
    r = c.post(root + "/generate", headers=h, json={"expected_version": r.json()["workflow"]["version"]})
    d = r.json()["workflow"]["latest_document"]
    url = root + f"/documents/{d['id']}/download"
    assert "<script>" not in c.get(url).text
    assert "&lt;script&gt;" in c.get(url).text
    with SessionLocal() as db:
        logs = db.scalars(select(AuditEvent).where(AuditEvent.actor_id == u["id"], AuditEvent.resource_type == "autoform")).all()
        assert logs and all("QA Client" not in a.details_json and "Example Street" not in a.details_json for a in logs)
        record = db.get(GeneratedDocument, d["id"])
        source = json.loads(record.source_json); source["fields"]["client_name"] = "Tampered"
        record.source_json = json.dumps(source); db.commit()
    assert c.get(url).status_code == 409


def test_saved_founder_dna_reuses_existing_engine_without_cross_customer_profile(env):
    c, h, u, _, root = env
    with SessionLocal() as db:
        db.add(FounderProfile(tenant_id=u["tenant_id"], user_id=u["id"], owner_id=u["id"],
            profile_json=json.dumps({"capital": 3000, "hours_per_week": 20, "experience_years": 2})))
        db.commit()
    dna = c.get(root).json()["assistant"]["founder_dna"]
    assert dna["status"] == "SAVED_CUSTOMER_PROFILE" and dna["assessment"]["capital_band"] == "micro"


def test_connections_standby_and_public_read_no_personal_information(env):
    c, h, _, _, root = env
    r = c.get(root + "/connections")
    assert r.status_code == 200 and r.json()["external_actions_authorized"] is False
    assert any(x["status"] == "NO_SUBMISSION_ADAPTER" for x in r.json()["connections"])
    assert c.post(root + "/connections/public-check").status_code == 403
    with patch("app.services.external_readiness.urlopen", side_effect=OSError("provider failure")):
        r = c.post(root + "/connections/public-check", headers=h, json={})
    assert r.json()["status"] == "UNAVAILABLE_NOT_VERIFIED" and r.json()["notices"] == []


def test_unsupported_business_and_duplicate_start_are_explicit(env):
    c, h, u, p, root = env
    w = started(c, h, root)
    assert c.post(root + "/documents", headers=h, json={"template_key": "cleaning_service_agreement"}).json()["workflow"]["id"] == w["id"]
    assert c.post(root + "/documents", headers=h, json={"template_key": "government_form"}).status_code == 422
    from app.models import BusinessIdea
    with SessionLocal() as db:
        from app.models import BusinessProject
        project = db.get(BusinessProject, p["id"])
        idea = db.get(BusinessIdea, project.idea_id)
        fields = json.loads(idea.facts_json)
        fields.update(concept="Run a bakery", industry="food")
        idea.facts_json = json.dumps(fields); db.commit()
    assert c.get(root).json()["supported"] is False
