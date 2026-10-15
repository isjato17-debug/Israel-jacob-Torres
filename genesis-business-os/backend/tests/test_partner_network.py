"""Disposable HTTP lifecycle tests: no partner APIs, filings, ads or financial operations."""
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app, buckets
from app.config import settings
from app.db import SessionLocal
from app.models import User, SessionRecord, AuditEvent, Tenant


def account():
    c = TestClient(app)
    r = c.post("/api/auth/register", json={
        "email": f"partner-{uuid4().hex}@example.com", "tenant_name": "Disposable partner QA",
        "password": "Private-partner-test-2026!",
    })
    assert r.status_code == 200, r.text
    return c, {"X-CSRF-Token": r.json()["csrf"]}, r.json()["user"]


@pytest.fixture(scope="module")
def accounts():
    buckets.clear()
    owner, member, outsider = account(), account(), account()
    with SessionLocal() as db:
        db.get(User, member[2]["id"]).tenant_id = owner[2]["tenant_id"]
        for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == member[2]["id"])):
            session.tenant_id = owner[2]["tenant_id"]
        db.commit()
    yield owner, member, outsider
    for c, _, _ in (owner, member, outsider):
        c.close()


@pytest.fixture(autouse=True)
def reset_limits():
    buckets.clear()


@pytest.fixture()
def network(accounts, monkeypatch):
    owner, member, outsider = accounts
    monkeypatch.setattr(settings, "platform_owner_user_ids", owner[2]["id"])
    return owner, member, outsider


def body(**changes):
    return {
        "business_name": "Private Partner", "contact_name": "QA Contact",
        "contact_email": "private-qa@example.com", "category": "legal",
        "services": "Reviewed business legal support", "coverage": ["NY", "DC"],
        "professional_credentials": "Self-reported professional credentials",
        "license_information": "Self-reported license; not independently verified",
        "api_capabilities": "None connected", "partnership_interests": "Manual reviewed delivery",
        "pricing_information": "Indicative only; no charge authorized", "consent": True, **changes,
    }


def create(who, **changes):
    c, h, _ = who
    r = c.post("/api/v2/partners/applications", headers=h, json=body(**changes))
    assert r.status_code == 200, r.text
    return r.json()


def review(owner, item, action, **changes):
    c, h, _ = owner
    return c.post(f"/api/v2/operator/partners/{item['id']}/review", headers=h, json={
        "action": action, "expected_version": item["version"], "confirm": True, **changes,
    })


def approved(owner, member):
    item = create(member)
    for action, extra in [
        ("begin_review", {}), ("verify", {"reference": "Manual licensing review fixture"}),
        ("await_agreement", {}), ("record_agreement", {"reference": "Accepted agreement fixture"}),
        ("approve", {}),
    ]:
        r = review(owner, item, action, **extra)
        assert r.status_code == 200, r.text
        item = r.json()
    return item


def test_catalog_distinguishes_information_from_connections():
    c = TestClient(app)
    result = c.get("/api/v2/partners/catalog").json()
    assert len(result["categories"]) == 12
    assert len(result["jurisdictions"]) == 51
    assert any(x["code"] == "DC" for x in result["jurisdictions"])
    assert "ACTIVE" in result["statuses"]
    assert all(not value for value in result["capabilities"].values())
    assert all(x["manual_verification_required"] and not x["filing_enabled"] for x in result["jurisdictions"])
    assert all(x["connection_type"] == "OFFICIAL_PUBLIC_INFORMATION" for x in result["official_resources"])
    c.close()


def test_applicant_is_never_automatically_verified_and_private(network):
    owner, member, outsider = network
    item = create(member)
    assert item["status"] == "APPLICATION"
    assert item["verification_status"] == "NOT_VERIFIED"
    assert "review" not in item
    assert item["verified_performance"] is None and not item["external_actions_enabled"]
    assert item["id"] in [x["id"] for x in member[0].get("/api/v2/partners/applications").json()["applications"]]
    assert item["id"] not in [x["id"] for x in owner[0].get("/api/v2/partners/applications").json()["applications"]]
    assert outsider[0].get(f"/api/v2/partners/applications/{item['id']}/history").status_code == 404
    operator_items = owner[0].get("/api/v2/operator/partners").json()["applications"]
    assert item["id"] in [x["id"] for x in operator_items]
    reviewed = next(x for x in operator_items if x["id"] == item["id"])
    assert reviewed["review"]["evidence"] == [] and reviewed["review"]["valid"] is False


def test_default_deny_owner_role_is_not_platform_owner(accounts, monkeypatch):
    owner, _, _ = accounts
    monkeypatch.setattr(settings, "platform_owner_user_ids", "")
    assert owner[0].get("/api/v2/operator/partners").status_code == 403
    assert owner[0].get("/api/v2/operator/partner-promotions").status_code == 403


def test_operator_remains_tenant_scoped(network, monkeypatch):
    owner, member, outsider = network
    item = create(member)
    monkeypatch.setattr(settings, "platform_owner_user_ids", outsider[2]["id"])
    assert outsider[0].get("/api/v2/operator/partners").json()["applications"] == []
    assert review(outsider, item, "begin_review").status_code == 404


@pytest.mark.parametrize("changes", [
    {"consent": False}, {"category": "invented"}, {"coverage": ["XX"]},
    {"coverage": ["NY", "NY"]}, {"business_name": " "}, {"contact_email": "invalid"},
    {"services": "x" * 2001}, {"api_key": "must-not-be-accepted"}, {"status": "VERIFIED"},
])
def test_validation_and_no_client_status_injection(network, changes):
    _, member, _ = network
    assert member[0].post("/api/v2/partners/applications", headers=member[1], json=body(**changes)).status_code == 422


def test_auth_csrf_and_lockdown(network):
    owner, member, _ = network
    anon = TestClient(app)
    assert anon.get("/api/v2/partners/applications").status_code == 401
    assert member[0].post("/api/v2/partners/applications", json=body()).status_code == 403
    item = create(member)
    assert member[0].post(f"/api/v2/operator/partners/{item['id']}/review", headers=member[1], json={
        "action": "begin_review", "expected_version": 1, "confirm": True,
    }).status_code == 403
    with SessionLocal() as db:
        db.get(Tenant, owner[2]["tenant_id"]).lockdown = True
        db.commit()
    try:
        assert review(owner, item, "begin_review").status_code == 423
        assert member[0].patch(f"/api/v2/partners/applications/{item['id']}", headers=member[1], json={
            **body(), "expected_version": item["version"],
        }).status_code == 423
    finally:
        with SessionLocal() as db:
            db.get(Tenant, owner[2]["tenant_id"]).lockdown = False
            db.commit()
    anon.close()


def test_review_evidence_agreement_and_activation_guards(network):
    owner, member, _ = network
    item = create(member)
    assert review(owner, item, "verify", reference="Fake shortcut").status_code == 409
    assert review(owner, item, "begin_review", confirm=False).status_code == 422
    r = review(owner, item, "begin_review")
    assert r.status_code == 200
    item = r.json()
    assert review(owner, item, "verify").status_code == 422
    assert review(owner, item, "request_information").status_code == 422
    item = review(owner, item, "request_information", note="Please provide license details").json()
    assert item["status"] == "VERIFICATION_REQUIRED"
    item = review(owner, item, "verify", reference="Operator reviewed official license record").json()
    assert item["verification_status"] == "MANUAL_REVIEW_RECORDED"
    item = review(owner, item, "await_agreement").json()
    assert review(owner, item, "approve").status_code == 409
    item = review(owner, item, "record_agreement", reference="Accepted agreement manual record").json()
    item = review(owner, item, "approve").json()
    assert item["status"] == "APPROVED"
    item = review(owner, item, "begin_integration").json()
    item = review(owner, item, "record_integration", reference="Offline adapter contract test").json()
    assert item["integration_status"] == "TEST_EVIDENCE_RECORDED"
    assert review(owner, item, "activate", reference="Not authorization").status_code == 409
    assert not item["external_actions_enabled"]


def test_edit_invalidation_stale_protection_and_audit_minimization(network):
    owner, member, _ = network
    item = approved(owner, member)
    r = member[0].patch(f"/api/v2/partners/applications/{item['id']}", headers=member[1], json={
        **body(services="Updated private business service"), "expected_version": item["version"],
    })
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "APPLICATION" and r.json()["verification_status"] == "NOT_VERIFIED"
    assert review(owner, item, "begin_integration").status_code == 409
    current = next(x for x in owner[0].get("/api/v2/operator/partners").json()["applications"] if x["id"] == item["id"])
    assert current["review"]["evidence"] and not current["review"]["valid"]
    events = owner[0].get(f"/api/v2/operator/partners/{item['id']}/history").json()["events"]
    assert len(events) >= 7
    assert all(set(x["details"]) == {"status", "version"} for x in events)
    with SessionLocal() as db:
        audit_rows = db.scalars(select(AuditEvent).where(AuditEvent.resource_id == item["id"])).all()
        assert all("private-qa" not in row.details_json and "Updated private" not in row.details_json for row in audit_rows)


def test_suspend_reopen_requires_fresh_verification(network):
    owner, member, _ = network
    item = approved(owner, member)
    item = review(owner, item, "suspend", note="Manual credential recheck required").json()
    assert item["status"] == "SUSPENDED" and item["verification_status"] == "NOT_VERIFIED"
    assert member[0].patch(f"/api/v2/partners/applications/{item['id']}", headers=member[1], json={
        **body(), "expected_version": item["version"],
    }).status_code == 409
    item = review(owner, item, "reopen").json()
    assert item["status"] == "UNDER_REVIEW"
    assert review(owner, item, "approve").status_code == 409
    item = review(owner, item, "reject", note="Eligibility evidence insufficient").json()
    assert item["status"] == "REJECTED"


def test_promotion_requires_partner_and_permission_and_never_publishes(network):
    owner, member, outsider = network
    item = approved(owner, member)
    c, h, _ = owner
    payload = {"partner_id": item["id"], "title": "Co-marketing planning",
               "content": "Original draft pending partner permission", "consent": True}
    r = c.post("/api/v2/operator/partner-promotions", headers=h, json=payload)
    assert r.status_code == 200, r.text
    no_permission = r.json()
    endpoint = f"/api/v2/operator/partner-promotions/{no_permission['id']}/review"
    assert c.post(endpoint, headers=h, json={"action": "approve", "confirm": True,
                                           "expected_version": no_permission["version"]}).status_code == 409
    r = c.post("/api/v2/operator/partner-promotions", headers=h, json={
        **payload, "partner_permission_reference": "Partner-approved co-branding record",
    })
    promotion = r.json()
    endpoint = f"/api/v2/operator/partner-promotions/{promotion['id']}/review"
    result = c.post(endpoint, headers=h, json={"action": "approve", "confirm": True,
                                             "expected_version": promotion["version"]})
    assert result.status_code == 200, result.text
    approved_plan = result.json()
    assert approved_plan["status"] == "APPROVED" and not approved_plan["publishing_enabled"]
    assert approved_plan["verified_performance"] is None and not approved_plan["commission_authorized"]
    assert not approved_plan["referral_collection_enabled"]
    changed_partner = member[0].patch(f"/api/v2/partners/applications/{item['id']}", headers=member[1], json={
        **body(services="Changed after promotion review"), "expected_version": item["version"],
    })
    assert changed_partner.status_code == 200
    revised_plan = next(p for p in c.get("/api/v2/operator/partner-promotions").json()["promotions"]
                        if p["id"] == promotion["id"])
    assert revised_plan["status"] == "DRAFT" and revised_plan["version"] == approved_plan["version"] + 1
    assert c.post(endpoint, headers=h, json={"action": "approve", "confirm": True,
                                           "expected_version": revised_plan["version"]}).status_code == 409
    assert c.post(endpoint, headers=h, json={"action": "archive", "confirm": True,
                                           "expected_version": promotion["version"]}).status_code == 409
    assert c.post(endpoint, headers=h, json={"action": "archive", "confirm": True,
                                           "expected_version": revised_plan["version"]}).json()["status"] == "ARCHIVED"
    assert outsider[0].get("/api/v2/operator/partner-promotions").status_code == 403
