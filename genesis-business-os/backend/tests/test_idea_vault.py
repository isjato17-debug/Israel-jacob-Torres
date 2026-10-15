"""M1 acceptance and financial/isolation regressions; all data is disposable."""
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app, buckets
from app.db import SessionLocal
from app.models import AuditEvent, BusinessIdea, BusinessProject, IdeaRevision, SessionRecord, Tenant, User
from test_big_consultation import account
from app.services.idea_planning import prepare_plans
from app.v2.partner_contracts import CATEGORIES

FACTS = {
    "concept": "I want to start a cleaning business in New York with $3,000.",
    "industry": "cleaning", "jurisdiction": "NY", "budget_cents": 300000,
    "goals": "Build repeat local clients", "preferences": "Start owner-operated",
    "notes": "Keep my startup budget", "assumptions": "Need local quotes",
}


@pytest.fixture()
def env():
    buckets.clear()
    c, h, u = account()
    yield c, h, u
    c.close()


def create(c, h, **extra):
    r = c.post("/api/v2/ideas", headers=h, json={**FACTS, "consent": True, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def action(c, h, idea, verb, **extra):
    return c.post(f"/api/v2/ideas/{idea['id']}/{verb}", headers=h,
                  json={"expected_version": idea["version"], **extra})


def develop(c, h):
    idea = create(c, h)
    idea = action(c, h, idea, "generate").json()
    idea = action(c, h, idea, "select", plan_key="start_smart").json()
    r = action(c, h, idea, "develop")
    assert r.status_code == 200, r.text
    return idea, r.json()


def test_exact_cleaning_acceptance_and_persistent_project(env):
    c, h, u = env
    with patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")):
        idea = create(c, h)
        assert idea["budget_cents"] == 300000
        planned = action(c, h, idea, "generate")
        assert planned.status_code == 200, planned.text
        idea = planned.json()
    plans = idea["plans"]
    assert [p["name"] for p in plans] == ["Start Smart", "Build Strong", "Grow Big"]
    assert len({p["startup_total_cents"] for p in plans}) == 3
    assert len({p["monthly_units"] for p in plans}) == 3
    assert plans[0]["funding_gap_cents"] == 0
    assert plans[1]["funding_gap_cents"] > 0
    assert plans[2]["funding_gap_cents"] > plans[1]["funding_gap_cents"]
    for p in plans:
        assert sum(i["amount_cents"] for i in p["startup_items"]) == p["startup_total_cents"]
        assert sum(i["amount_cents"] for i in p["monthly_items"]) == p["monthly_fixed_cents"]
        assert p["monthly_revenue_cents"] == p["average_ticket_cents"] * p["monthly_units"]
        assert p["funding_required_cents"] == p["startup_total_cents"] + p["reserve_cents"]
        assert p["funding_gap_cents"] == max(0, p["funding_required_cents"] - 300000)
        assert len(p["revenue_scenarios"]) == 3 and p["assumptions"]
        assert any(r["official_url"] == "https://www.businessexpress.ny.gov/" for r in p["requirements"])
        assert any("cleaning-chemical" in r["title"] for r in p["requirements"])
        assert {"insurance", "tax", "legal"} <= {x["category"] for x in p["service_needs"]}
    assert sum(p["recommended"] for p in plans) == 1
    # Customers can choose a non-recommended plan; the gap remains visible.
    selected = action(c, h, idea, "select", plan_key="build_strong").json()
    r = action(c, h, selected, "develop")
    assert r.status_code == 200, r.text
    project = r.json()
    assert project["budget_cents"] == 300000 and project["plan"]["key"] == "build_strong"
    assert project["stage"] == "PLANNING" and len(project["checklist"]) == 7
    assert all(t["budget"] == 0 for t in project["checklist"])
    assert action(c, h, selected, "develop").json()["id"] == project["id"]
    task = project["checklist"][0]
    assert c.patch(f"/api/businesses/{project['business_id']}/execution/{task['id']}",
                   headers=h, json={"status": "done"}).status_code == 200
    assert c.get(f"/api/v2/projects/{project['id']}").json()["checklist"][0]["status"] == "done"
    assert c.get(f"/api/businesses/{project['business_id']}/command-center").status_code == 200
    assert c.post("/api/auth/logout", headers=h).status_code == 200
    assert c.get(f"/api/v2/projects/{project['id']}").status_code == 401
    logged = c.post("/api/auth/login", json={"email": u["email"], "password": "BIG-foundation-safe-2026!"})
    assert logged.status_code == 200
    assert c.get(f"/api/v2/ideas/{idea['id']}").json()["project_id"] == project["id"]
    assert c.get("/api/v2/projects").json()["projects"][0]["budget_cents"] == 300000


def test_create_edit_multiple_archive_restore_and_version_history(env):
    c, h, _ = env
    first = create(c, h); other = create(c, h, concept="A different consulting idea", budget_cents=100001)
    assert other["id"] != first["id"]
    prepared = action(c, h, first, "generate").json()
    chosen = action(c, h, prepared, "select", plan_key="grow_big").json()
    assert action(c, h, prepared, "select", plan_key="start_smart").status_code == 409
    edited = c.patch(f"/api/v2/ideas/{first['id']}", headers=h,
                     json={**FACTS, "budget_cents": 123456, "expected_version": chosen["version"]})
    assert edited.status_code == 200, edited.text
    edited = edited.json()
    assert not edited["plans"] and edited["selected_plan"] is None
    archived = action(c, h, edited, "archive").json()
    assert action(c, h, archived, "generate").status_code == 409
    restored = action(c, h, archived, "restore").json()
    assert restored["budget_cents"] == 123456 and restored["status"] == "DRAFT"
    assert len(restored["history"]) == restored["version"]
    assert c.get("/api/v2/ideas").json()["ideas"]
    with SessionLocal() as db:
        revisions = db.scalars(select(IdeaRevision).where(IdeaRevision.idea_id == first["id"])).all()
        assert json.loads(revisions[0].facts_json)["budget_cents"] == 300000
        audit = db.scalars(select(AuditEvent).where(AuditEvent.resource_id == first["id"])).all()
        assert all("cleaning" not in r.details_json and "300000" not in r.details_json for r in audit)


@pytest.mark.parametrize("extra", [
    {"consent": False}, {"budget_cents": True}, {"budget_cents": -1}, {"budget_cents": 1.2},
    {"budget_cents": 100000001}, {"jurisdiction": "XX"}, {"concept": "   "},
    {"user_id": "fake"}, {"status": "APPROVED"},
])
def test_invalid_and_identity_injection_rejected(env, extra):
    c, h, _ = env
    assert c.post("/api/v2/ideas", headers=h, json={**FACTS, "consent": True, **extra}).status_code == 422


def test_auth_csrf_lockdown_and_same_tenant_customer_isolation(env):
    c, h, u = env
    anonymous = TestClient(app)
    assert anonymous.get("/api/v2/ideas").status_code == 401
    assert c.post("/api/v2/ideas", json={**FACTS, "consent": True}).status_code == 403
    idea, project = develop(c, h)
    outsider, oh, ou = account()
    for same_tenant in (False, True):
        if same_tenant:
            with SessionLocal() as db:
                db.get(User, ou["id"]).tenant_id = u["tenant_id"]
                for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == ou["id"])):
                    session.tenant_id = u["tenant_id"]
                db.commit()
        assert outsider.get(f"/api/v2/ideas/{idea['id']}").status_code == 404
        assert action(outsider, oh, idea, "archive").status_code == 404
        assert outsider.get(f"/api/v2/projects/{project['id']}").status_code == 404
        for endpoint in ("command-center", "battle", "failure-lab", "execution", "plan-vs-actual", "decision-ledger", "actions"):
            assert outsider.get(f"/api/businesses/{project['business_id']}/{endpoint}").status_code in (403, 404)
        assert not any(x["id"] == project["business_id"] for x in outsider.get("/api/businesses").json())
        assert outsider.get("/api/v2/ideas").json()["ideas"] == []
        assert outsider.get("/api/v2/projects").json()["projects"] == []
    with SessionLocal() as db:
        db.get(Tenant, u["tenant_id"]).lockdown = True; db.commit()
    assert action(c, h, idea, "develop").status_code == 423
    assert c.post("/api/v2/ideas", headers=h, json={**FACTS, "consent": True}).status_code == 423
    outsider.close(); anonymous.close()


def test_developed_plan_is_immutable_and_archive_restores_link(env):
    c, h, _ = env
    initial, project = develop(c, h)
    idea = c.get(f"/api/v2/ideas/{initial['id']}").json()
    assert action(c, h, idea, "generate").status_code == 409
    assert c.patch(f"/api/v2/ideas/{idea['id']}", headers=h,
                   json={**FACTS, "expected_version": idea["version"]}).status_code == 409
    archived = action(c, h, idea, "archive").json()
    restored = action(c, h, archived, "restore").json()
    assert restored["status"] == "DEVELOPED" and restored["project_id"] == project["id"]


@pytest.mark.parametrize("budget", [0, 1, 300001, 100000000])
def test_estimate_arithmetic_provenance_and_reused_partner_vocabulary(budget):
    plans = prepare_plans({**FACTS, "budget_cents": budget})
    for p in plans:
        assert p["available_budget_cents"] == budget
        assert p["funding_gap_cents"] == max(0, p["funding_required_cents"] - budget)
        assert p["classification"] == "SYSTEM_CALCULATED_FROM_UNVERIFIED_ESTIMATES"
        assert all(s["category"] in dict(CATEGORIES) for s in p["service_needs"])
        for s in p["revenue_scenarios"]:
            expected = round(s["revenue_cents"] * p["gross_margin"] - p["monthly_fixed_cents"])
            assert abs(s["operating_profit_cents"] - expected) <= 1


def test_bakery_assessment_does_not_reuse_cleaning_specific_guidance():
    plans = prepare_plans({**FACTS, "concept": "Start a home bakery in New York", "industry": "bakery"})
    for p in plans:
        assert "Food" in p["business_model"]
        assert any("food-business" in r["title"] for r in p["requirements"])
        assert not any("cleaning" in r["title"].lower() + r["reason"].lower() for r in p["requirements"])
