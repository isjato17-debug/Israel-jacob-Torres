"""Atomic application budgets. Simulated accounting only; external transport stays OFF.

Unknown/interrupted costs retain reservations. There is no timeout-based release.
Micro-USD integer arithmetic avoids floating point money. No provider SDK is imported.
"""
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import select, update, func
from ..models import AICostPolicy, AIBudgetBucket, AICostReservation, AuditEvent
from .intelligence_contracts import StrictContract
from .document_engine import canonical
from .test_signing import sha

PHASE_EXTERNAL_SPENDING_AUTHORIZED_MICROUSD = 0
MODE = "SIMULATED_FINANCIAL_CONTROL_NOT_PROVIDER_BILLING"


class Limits(StrictContract):
    request: int = Field(default=0, ge=0, le=10**12)
    task: int = Field(default=0, ge=0, le=10**12)
    customer: int = Field(default=0, ge=0, le=10**12)
    daily: int = Field(default=0, ge=0, le=10**12)
    monthly: int = Field(default=0, ge=0, le=10**12)


class PolicyInput(StrictContract):
    expected_version: int = Field(ge=0)
    shutdown: bool = True
    simulation_enabled: bool = False
    paid_provider_enabled: bool = False
    limits: Limits = Field(default_factory=Limits)
    allowed_models: list[str] = Field(default_factory=lambda: ["mock-budget-v1"], min_length=1, max_length=1)
    concurrency_limit: int = Field(default=1, ge=1, le=20)
    retry_ceiling: int = Field(default=1, ge=1, le=3)


class Usage(StrictContract):
    input_tokens: int = Field(ge=0, le=10**8)
    output_tokens: int = Field(ge=0, le=10**8)
    actual_microusd: int = Field(ge=0, le=10**12)


class Reserve(StrictContract):
    request_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{16,80}$")
    model: str = "mock-budget-v1"
    input_token_ceiling: int = Field(ge=1, le=10**6)
    output_token_ceiling: int = Field(ge=1, le=10**6)
    attempt: int = Field(default=1, ge=1, le=3)


def event(db, user, action, resource, **details):
    db.add(AuditEvent(tenant_id=user.tenant_id, actor_id=user.id, action=action,
                     resource_type="ai_finance", resource_id=resource,
                     details_json=canonical({"mode": MODE, **details})))


def describe(db):
    p = db.get(AICostPolicy, "global")
    buckets = db.scalars(select(AIBudgetBucket).order_by(AIBudgetBucket.scope)).all()
    return {"mode": MODE, "paid_provider_enabled": False, "actual_external_spending_microusd": 0,
            "version": p.version if p else 0, "shutdown": p.shutdown if p else True,
            "simulation_enabled": p.simulation_enabled if p else False,
            "limits": json.loads(p.limits_json) if p else Limits().model_dump(),
            "allowed_models": json.loads(p.allowed_models_json) if p else ["mock-budget-v1"],
            "concurrency_limit": p.concurrency_limit if p else 1,
            "retry_ceiling": p.retry_ceiling if p else 1,
            "buckets": [{"scope": b.scope, "reserved_microusd": b.reserved_microusd,
                         "spent_microusd": b.spent_microusd} for b in buckets],
            "rate_notice": "Virtual test rate $1/M input + $4/M output. NOT an official provider quote.",
            "residual_exposure": "Future provider billing delays, price changes and overages cannot be eliminated. "
                                 "Unknown requests keep their full reservation until verified reconciliation."}


def configure(db, user, data):
    from ..v2.growth import is_platform_owner
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform-owner access required")
    if data.paid_provider_enabled:
        event(db, user, "ai_paid_activation_denied", "global")
        raise HTTPException(403, "Phase 2 paid AI is disabled; external spending authorization is $0")
    if data.allowed_models != ["mock-budget-v1"]:
        raise HTTPException(422, "Only the offline budget-test model is available in this phase")
    p = db.get(AICostPolicy, "global")
    if not p:
        if data.expected_version != 0:
            raise HTTPException(409, "Policy version changed")
        p = AICostPolicy(id="global", owner_id=user.id)
        db.add(p); db.flush()
    elif db.execute(update(AICostPolicy).where(AICostPolicy.id == "global",
                    AICostPolicy.version == data.expected_version).values(version=AICostPolicy.version + 1)).rowcount != 1:
        raise HTTPException(409, "Policy version changed")
    db.refresh(p)
    p.shutdown, p.simulation_enabled = data.shutdown, data.simulation_enabled
    p.limits_json, p.allowed_models_json = canonical(data.limits.model_dump()), canonical(data.allowed_models)
    p.concurrency_limit, p.retry_ceiling = data.concurrency_limit, data.retry_ceiling
    event(db, user, "ai_financial_policy_updated", p.id, version=p.version,
          paid_provider_enabled=False, shutdown=p.shutdown)
    db.flush()
    return p


def locked_policy(db):
    if db.execute(update(AICostPolicy).where(AICostPolicy.id == "global")
                  .values(version=AICostPolicy.version)).rowcount != 1:
        raise HTTPException(403, "No financial authorization exists")
    return db.get(AICostPolicy, "global", populate_existing=True)


def maximum_cost(data):
    # Deliberately conservative, reproducible VIRTUAL test tariff, never a live quote.
    return data.input_token_ceiling + 4 * data.output_token_ceiling


def reserve(db, user, project, data, *, paid=False):
    if paid:
        # Hard ceiling is independent of credentials, policy edits or environment flags.
        raise HTTPException(403, "Paid transport is disabled; no request or reservation was sent")
    if project.user_id != user.id or project.tenant_id != user.tenant_id:
        raise HTTPException(404, "Project not found")
    p = locked_policy(db)
    identity = {"customer": user.id, "task": project.id, **data.model_dump(exclude={"request_key", "attempt"})}
    fingerprint = sha(canonical(identity).encode())
    previous = db.scalar(select(AICostReservation).where(
        AICostReservation.owner_id == p.owner_id, AICostReservation.request_key == data.request_key))
    if previous:
        if previous.fingerprint != fingerprint:
            raise HTTPException(409, "A request key cannot be reused with different inputs")
        return previous
    if p.shutdown or not p.simulation_enabled:
        raise HTTPException(403, "Emergency shutdown is active or simulated usage is disabled")
    if data.model not in json.loads(p.allowed_models_json) or data.attempt > p.retry_ceiling:
        raise HTTPException(403, "Model or retry attempt not authorized")
    active = db.scalar(select(func.count()).select_from(AICostReservation).where(
        AICostReservation.owner_id == p.owner_id,
        AICostReservation.status.in_(("RESERVED", "UNCERTAIN"))))
    if active >= p.concurrency_limit:
        raise HTTPException(429, "Concurrent reservation limit reached")
    amount = maximum_cost(data)
    limits = Limits.model_validate_json(p.limits_json)
    if amount > limits.request:
        raise HTTPException(402, "Per-request maximum exceeds authorized budget")
    now = datetime.now(timezone.utc)
    scopes = {f"task:{project.id}":limits.task, f"customer:{user.id}":limits.customer,
              f"day:{now:%Y-%m-%d}":limits.daily, f"month:{now:%Y-%m}":limits.monthly}
    # The root policy lock serializes bucket creation, checked updates and request deduplication.
    # A nested transaction rolls back ALL scopes if any scope cannot cover the maximum.
    with db.begin_nested():
        for scope, cap in sorted(scopes.items()):
            b = db.scalar(select(AIBudgetBucket).where(
                AIBudgetBucket.owner_id == p.owner_id, AIBudgetBucket.scope == scope))
            if not b:
                b = AIBudgetBucket(owner_id=p.owner_id, scope=scope)
                db.add(b); db.flush()
            changed = db.execute(update(AIBudgetBucket).where(AIBudgetBucket.id == b.id,
                AIBudgetBucket.reserved_microusd + AIBudgetBucket.spent_microusd + amount <= cap)
                .values(reserved_microusd=AIBudgetBucket.reserved_microusd + amount)).rowcount
            if changed != 1:
                raise HTTPException(402, "Authorized budget exhausted; request rejected")
        reservation = AICostReservation(owner_id=p.owner_id, customer_id=user.id, task_id=project.id,
            request_key=data.request_key, fingerprint=fingerprint, model=data.model,
            scopes_json=canonical(list(scopes)), maximum_microusd=amount)
        db.add(reservation); db.flush()
        event(db, user, "ai_cost_reserved", reservation.id, maximum_microusd=amount)
    return reservation


def reconcile(db, user, reservation_id, usage=None):
    p = locked_policy(db)
    r = db.get(AICostReservation, reservation_id, populate_existing=True)
    if not r or r.owner_id != p.owner_id or r.customer_id != user.id:
        raise HTTPException(404, "Reservation not found")
    if usage is None:
        if r.status == "RESERVED":
            r.status = "UNCERTAIN"
            event(db, user, "ai_cost_uncertain", r.id, retained_microusd=r.maximum_microusd)
        return r
    if r.status == "SETTLED":
        if r.usage_json != canonical(usage.model_dump()):
            raise HTTPException(409, "Conflicting usage report; manual reconciliation required")
        return r
    for scope in json.loads(r.scopes_json):
        changed = db.execute(update(AIBudgetBucket).where(
            AIBudgetBucket.owner_id == r.owner_id, AIBudgetBucket.scope == scope,
            AIBudgetBucket.reserved_microusd >= r.maximum_microusd)
            .values(reserved_microusd=AIBudgetBucket.reserved_microusd - r.maximum_microusd,
                    spent_microusd=AIBudgetBucket.spent_microusd + usage.actual_microusd)).rowcount
        if changed != 1:
            raise HTTPException(409, "Budget ledger mismatch; no funds released")
    r.status, r.actual_microusd = "SETTLED", usage.actual_microusd
    r.usage_json = canonical(usage.model_dump())
    if usage.actual_microusd > r.maximum_microusd:
        p.shutdown = True
        event(db, user, "ai_cost_overrun_shutdown", r.id, maximum_microusd=r.maximum_microusd,
              reported_microusd=usage.actual_microusd)
    event(db, user, "ai_cost_reconciled", r.id, actual_microusd=usage.actual_microusd)
    db.flush()
    return r
