"""Unified business path: real existing services, isolated customer data, no external actions."""
import json
from unittest.mock import patch
import pytest
from sqlalchemy import select, func
from app.db import SessionLocal
from app.main import buckets
from app.models import BusinessIdea, BusinessProject, ExecutionTask, ProjectAction, User, SessionRecord, Tenant
from test_big_consultation import account, prepare, send
from test_idea_vault import FACTS, action

PASSWORD = "BIG-foundation-safe-2026!"


@pytest.fixture
def env():
    buckets.clear()
    c, h, u = account()
    j = prepare(c, h)
    j = c.patch(f"/api/v2/journeys/{j['id']}/answer", headers=h, json={
        "field": "goal", "value": FACTS["concept"], "expected_version": j["version"]}).json()
    result = send(c, h, j)
    assert result.status_code == 200, result.text
    yield c, h, u, j, result.json()
    c.close()


def bridge(env, **extra):
    c, h, _, j, consultation = env
    return c.post(f"/api/v2/journeys/{j['id']}/business-path", headers=h, json={
        "expected_version": j["version"], "consultation_version": consultation["version"],
        "privacy_version": 0, "budget_cents": 300000, "consent": True, **extra})


def chosen(env, strategy="focused_launch", financial="build_strong"):
    c, h, _, _, _ = env
    result = bridge(env)
    assert result.status_code == 200, result.text
    idea = result.json()
    result = action(c, h, idea, "strategy", strategy_key=strategy)
    assert result.status_code == 200, result.text
    idea = action(c, h, result.json(), "select", plan_key=financial).json()
    return idea


def test_goal_once_two_strategies_three_plans_auto_roadmap_and_resume(env):
    c, h, u, j, consultation = env
    root = f"/api/v2/journeys/{j['id']}/business-path"
    assert c.get(root).json()["concept"] == FACTS["concept"]
    with patch("urllib.request.urlopen", side_effect=AssertionError("Native handoff must not use network")):
        idea = chosen(env)
        result = action(c, h, idea, "develop")
    assert result.status_code == 200, result.text
    project = result.json()
    assert idea["concept"] == FACTS["concept"] and idea["jurisdiction"] == "NY"
    assert [p["name"] for p in idea["plans"]] == ["Start Smart", "Build Strong", "Grow Big"]
    assert len(idea["strategies"]) == 2 and sum(s["preferred"] for s in idea["strategies"]) == 1
    for option in idea["strategies"]:
        assert option["advantages"] and option["disadvantages"] and option["reason"]
        assert option["classification"] == "DETERMINISTIC_FROM_UNVERIFIED_INPUTS_NOT_LIVE_AI"
    assert project["budget_cents"] == 300000 and project["plan"]["key"] == "build_strong"
    assert project["plan"]["business_strategy"] == idea["selected_strategy"]
    assert project["plan"]["source_context"]["journey_id"] == j["id"]
    assert project["plan"]["source_context"]["consultation_version"] == consultation["version"]
    orchestrator = f"/api/v2/projects/{project['id']}/orchestrator"
    view = c.get(orchestrator).json()
    assert view["initialized"] and len(view["actions"]) == 5
    assert next(a for a in view["actions"] if a["key"] == "strategy")["status"] == "COMPLETED_VERIFIED"
    assert view["next_action"]["key"] == "unified:strategy" and len(view["planning_tasks"]) == 2
    assert all(t["budget"] == 0 for t in project["checklist"])
    for next_key in ("unified:strategy", "unified:funding"):
        view = c.get(orchestrator).json()
        assert view["next_action"]["key"] == next_key
        task = view["next_action"]["task_id"]
        r = c.patch(f"/api/businesses/{project['business_id']}/execution/{task}", headers=h, json={"status": "done"})
        assert r.status_code == 200, r.text
    assert c.get(orchestrator).json()["next_action"]["key"] == "prepare"
    assert action(c, h, idea, "develop").json()["id"] == project["id"]
    assert bridge(env).json()["id"] == idea["id"]  # Retry never copies or starts a second system.
    assert c.post("/api/auth/logout", headers=h).status_code == 200
    assert c.get(orchestrator).status_code == 401
    assert c.post("/api/auth/login", json={"email": u["email"], "password": PASSWORD}).status_code == 200
    restored = c.get(orchestrator).json()
    assert restored["business_strategy"] == idea["selected_strategy"]
    assert restored["next_action"]["key"] == "prepare"
    assert c.get(root).json()["idea"]["project_id"] == project["id"]
    assert c.get(f"/api/v2/journeys/{j['id']}/consultation").json()["consultation"]["context_stale"] is False


@pytest.mark.parametrize("strategy", ["focused_launch", "contract_first"])
@pytest.mark.parametrize("financial", ["start_smart", "build_strong", "grow_big"])
def test_either_strategy_independent_of_all_three_financial_plans(env, strategy, financial):
    c, h, _, _, _ = env
    idea = chosen(env, strategy, financial)
    project = action(c, h, idea, "develop").json()
    assert project["plan"]["key"] == financial
    assert project["plan"]["business_strategy"]["key"] == strategy
    assert project["budget_cents"] == 300000
    assert c.get(f"/api/v2/projects/{project['id']}/orchestrator").json()["initialized"]
    assert action(c, h, c.get(f"/api/v2/ideas/{idea['id']}").json(), "strategy",
                  strategy_key="focused_launch").status_code == 409


def test_separate_copy_consent_staleness_bounds_csrf_and_no_implicit_strategy(env):
    c, h, _, j, cons = env
    for extra in ({"consent": False}, {"budget_cents": True}, {"budget_cents": -1}, {"budget_cents": 3.5},
                  {"budget_cents": 100_000_001}, {"selected_strategy": "focused_launch"}):
        assert bridge(env, **extra).status_code == 422
    assert bridge(env, expected_version=j["version"]-1).status_code == 409
    assert bridge(env, consultation_version=999).status_code == 409
    assert bridge(env, privacy_version=999).status_code == 409
    root = f"/api/v2/journeys/{j['id']}/business-path"
    assert c.post(root, json={"expected_version": j["version"], "consultation_version": cons["version"],
                             "privacy_version": 0, "budget_cents": 300000, "consent": True}).status_code == 403
    assert c.get(root).json()["idea"] is None
    idea = bridge(env).json()
    idea = action(c, h, idea, "select", plan_key="build_strong").json()
    assert action(c, h, idea, "develop").status_code == 409
    assert idea["selected_strategy"] is None
    assert action(c, h, idea, "strategy", strategy_key="invented").status_code == 422
    assert action(c, h, idea, "strategy", strategy_key="focused_launch", expected_version=999).status_code == 409


def test_edit_resets_decision_not_source_and_snapshot_is_not_reinterpreted(env):
    c, h, _, j, _ = env
    idea = chosen(env)
    r = c.patch(f"/api/v2/ideas/{idea['id']}", headers=h, json={
        **FACTS, "expected_version": idea["version"], "goals": "Test commercial contracts"})
    assert r.status_code == 200, r.text
    edited = r.json()
    assert edited["selected_strategy"] is None and edited["plans"] == [] and edited["selected_plan"] is None
    assert edited["_source"]["journey_id"] == j["id"]


def test_private_same_tenant_cross_tenant_and_task_isolation(env):
    c, h, u, j, _ = env
    idea = chosen(env)
    project = action(c, h, idea, "develop").json()
    other, oh, ou = account()
    task = next(t for t in project["checklist"] if t["kpi"] == "unified:strategy")
    for same_tenant in (False, True):
        if same_tenant:
            with SessionLocal() as db:
                db.get(User, ou["id"]).tenant_id = u["tenant_id"]
                for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == ou["id"])):
                    session.tenant_id = u["tenant_id"]
                db.commit()
        assert other.get(f"/api/v2/journeys/{j['id']}/business-path").status_code == 404
        assert other.post(f"/api/v2/journeys/{j['id']}/business-path", headers=oh, json={
            "expected_version": j["version"], "consultation_version": 1, "privacy_version": 0,
            "budget_cents": 300000, "consent": True}).status_code == 404
        assert other.post(f"/api/v2/ideas/{idea['id']}/strategy", headers=oh, json={
            "expected_version": idea["version"], "strategy_key": "focused_launch"}).status_code == 404
        assert other.get(f"/api/v2/projects/{project['id']}/orchestrator").status_code == 404
        assert other.patch(f"/api/businesses/{project['business_id']}/execution/{task['id']}",
                           headers=oh, json={"status": "done"}).status_code == 404
    other.close()


def test_revocation_and_lockdown_stop_new_handoff(env):
    c, h, u, j, cons = env
    r = c.post(f"/api/v2/journeys/{j['id']}/consultation/privacy", headers=h, json={
        "action": "revoke", "expected_version": 0, "consultation_version": cons["version"], "confirmed": True})
    assert r.status_code == 200
    assert bridge(env).status_code == 409
    with SessionLocal() as db:
        db.get(Tenant, u["tenant_id"]).lockdown = True; db.commit()
    assert bridge(env).status_code == 423
