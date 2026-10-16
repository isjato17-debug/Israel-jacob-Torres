import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, func
from app.db import SessionLocal
from app.config import settings
from app.models import User, BusinessProject, AICostPolicy, AIBudgetBucket, AICostReservation, AuditEvent
from app.services import ai_finance as finance
from test_unified_intelligence import env
from test_project_execution import create
from test_big_consultation import account


@pytest.fixture
def setup(env, monkeypatch):
    c, h, user, _, _ = env
    p, _, _ = create(env)
    monkeypatch.setattr(settings, "platform_owner_user_ids", user["id"])
    # This is a disposable test database shared by tests; delete only this new feature's fixture rows.
    with SessionLocal() as db:
        for cls in (AICostReservation, AIBudgetBucket, AICostPolicy):
            db.query(cls).delete()
        u = db.get(User, user["id"])
        finance.configure(db, u, finance.PolicyInput(expected_version=0, shutdown=False, simulation_enabled=True,
            concurrency_limit=20, limits=finance.Limits(request=1000, task=1000, customer=1000,
                                                      daily=1000, monthly=1000)))
        db.commit()
    return c, h, user, p


def request(**extra):
    return finance.Reserve(request_key=str(uuid.uuid4()), input_token_ceiling=20,
                           output_token_ceiling=20, **extra)


@pytest.mark.parametrize("scope", ["request", "task", "customer", "daily", "monthly"])
def test_each_zero_budget_and_exhaustion_fail_closed(setup, scope):
    _, _, user, project = setup
    with SessionLocal() as db:
        p = db.get(AICostPolicy, "global")
        values = finance.Limits.model_validate_json(p.limits_json).model_dump()
        values[scope] = 0
        p.limits_json = finance.canonical(values); db.commit()
        with pytest.raises(HTTPException) as error:
            finance.reserve(db, db.get(User,user["id"]), db.get(BusinessProject,project["id"]), request())
        assert error.value.status_code == 402
        db.rollback()
        assert db.scalar(select(func.count()).select_from(AICostReservation)) == 0
        assert sum(db.scalars(select(AIBudgetBucket.reserved_microusd))) == 0


def test_concurrent_reservations_never_overdraw(setup):
    _, _, user, project = setup
    with SessionLocal() as db:
        p = db.get(AICostPolicy, "global")
        p.limits_json = finance.canonical({k:200 for k in finance.Limits.model_fields}); db.commit()
    def worker(_):
        with SessionLocal() as db:
            try:
                result = finance.reserve(db, db.get(User,user["id"]), db.get(BusinessProject,project["id"]), request())
                db.commit(); return result.id
            except HTTPException as exc:
                db.rollback(); assert exc.status_code == 402; return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(worker, range(8)))
    assert len([v for v in outcomes if v]) == 2
    with SessionLocal() as db:
        assert all(b.reserved_microusd == 200 and b.spent_microusd == 0
                   for b in db.scalars(select(AIBudgetBucket)))


def test_duplicates_retry_storm_and_interruption_preserve_hold(setup):
    _, _, user, project = setup
    data = request()
    with SessionLocal() as db:
        u, p = db.get(User,user["id"]), db.get(BusinessProject,project["id"])
        first = finance.reserve(db,u,p,data); db.commit()
        for _ in range(12):
            assert finance.reserve(db,u,p,data).id == first.id
        finance.reconcile(db,u,first.id,None); db.commit()
        assert first.status == "UNCERTAIN"
    with SessionLocal() as db:
        r = db.scalar(select(AICostReservation))
        assert r.status == "UNCERTAIN" and r.maximum_microusd == 100
        assert all(v == 100 for v in db.scalars(select(AIBudgetBucket.reserved_microusd)))
        with pytest.raises(HTTPException):
            finance.reserve(db,db.get(User,user["id"]),db.get(BusinessProject,project["id"]),request(attempt=2))
        db.rollback()
        # Request-key collisions cannot charge a different task/context.
        changed = data.model_copy(update={"output_token_ceiling":21})
        with pytest.raises(HTTPException) as error:
            finance.reserve(db,db.get(User,user["id"]),db.get(BusinessProject,project["id"]),changed)
        assert error.value.status_code == 409


def test_reconciliation_idempotent_overage_shutdown_and_audit(setup):
    _, _, user, project = setup
    with SessionLocal() as db:
        u, p = db.get(User,user["id"]), db.get(BusinessProject,project["id"])
        r = finance.reserve(db,u,p,request()); db.commit()
        usage = finance.Usage(input_tokens=20, output_tokens=30, actual_microusd=140)
        finance.reconcile(db,u,r.id,usage); db.commit()
        assert db.get(AICostPolicy,"global").shutdown is True
        assert all(b.reserved_microusd == 0 and b.spent_microusd == 140
                   for b in db.scalars(select(AIBudgetBucket)))
        count = db.scalar(select(func.count()).select_from(AuditEvent))
        finance.reconcile(db,u,r.id,usage); db.commit()
        assert count == db.scalar(select(func.count()).select_from(AuditEvent))
        with pytest.raises(HTTPException):
            finance.reserve(db,u,p,request())
        db.rollback()
        with pytest.raises(HTTPException):
            finance.reconcile(db,u,r.id,finance.Usage(input_tokens=1,output_tokens=1,actual_microusd=1))


def test_rollback_before_commit_releases_only_uncommitted_reservation(setup):
    _, _, user, project = setup
    with SessionLocal() as db:
        finance.reserve(db,db.get(User,user["id"]),db.get(BusinessProject,project["id"]),request())
        db.rollback()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(AICostReservation)) == 0
        assert sum(db.scalars(select(AIBudgetBucket.reserved_microusd))) == 0


def test_unauthorized_activation_model_and_paid_transport(setup):
    c, h, user, project = setup
    url = "/api/v2/operator/ai-finance"
    other, oh, _ = account()
    assert other.get(url).status_code == 403
    assert other.put(url,headers=oh,json={"expected_version":1}).status_code == 403
    assert c.put(url,headers=h,json={"expected_version":1,"paid_provider_enabled":True}).status_code == 403
    assert c.get(url).json()["paid_provider_enabled"] is False
    assert c.put(url,json={"expected_version":1}).status_code == 403
    with SessionLocal() as db:
        u, p = db.get(User,user["id"]),db.get(BusinessProject,project["id"])
        with pytest.raises(HTTPException):
            finance.reserve(db,u,p,request(model="unrestricted-live"))
        db.rollback()
        with pytest.raises(HTTPException):
            finance.reserve(db,u,p,request(),paid=True)
        assert db.scalar(select(func.count()).select_from(AICostReservation)) == 0
    other.close()


@pytest.mark.parametrize("bad", [-1, True, "10", float("nan")])
def test_invalid_usage_reports_rejected(bad):
    with pytest.raises(ValidationError):
        finance.Usage(input_tokens=1,output_tokens=1,actual_microusd=bad)
