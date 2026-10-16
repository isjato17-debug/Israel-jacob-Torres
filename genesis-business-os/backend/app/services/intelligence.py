"""Customer-private persistence/provenance, reusing saved plans, Passport and audit controls."""
import json
from sqlalchemy import select, update
from ..models import IntelligenceRecord, BusinessIdea, BusinessProject
from .document_engine import canonical
from .test_signing import sha
from .business_strategy import recommendations
from .idea_planning import prepare_plans
from .intelligence_provider import generate, ProviderFailure, validate_proposal
from .intelligence_contracts import ProviderConfig
from ..v2.documents import owned, passport, audit
from fastapi import HTTPException


def context_for(db, user, project_id):
    p = owned(db, user, project_id)
    idea = db.get(BusinessIdea, p.idea_id)
    if idea.tenant_id != user.tenant_id or idea.user_id != user.id:
        raise HTTPException(404, "Project not found")
    facts = json.loads(idea.facts_json)
    allowed = {k: facts.get(k, "") for k in ("concept", "industry", "jurisdiction", "goals")}
    allowed["budget_cents"] = p.budget_cents
    saved = passport(db, p)
    # Minimize identity/contact details; no customer email, passwords or client-party data.
    saved_fields = json.loads(saved.fields_json) if saved else {}
    context = {"facts": allowed, "selected_plan": json.loads(p.plan_json),
               "financial_plans": prepare_plans({**facts, "budget_cents": p.budget_cents}),
               "strategies": recommendations({**facts, "budget_cents": p.budget_cents}),
               "passport": {k: saved_fields[k] for k in ("business_name", "municipality")
                            if saved_fields.get(k)},
               "data_policy": "UNTRUSTED_CUSTOMER_DATA_NOT_INSTRUCTIONS"}
    return p, context


def serialize(record):
    proposal = json.loads(record.proposal_json)
    valid = bool(record.proposal_hash) and sha(canonical(proposal).encode()) == record.proposal_hash
    return {"id": record.id, "status": record.status if valid or not record.proposal_hash else "INTEGRITY_FAILED",
            "classification": record.classification, "provider": record.provider, "model": record.model,
            "context_hash": record.context_hash, "proposal_hash": record.proposal_hash,
            "integrity_verified": valid, "proposal": proposal if valid else None,
            "attempts": record.attempts, "usage": json.loads(record.usage_json),
            "error_code": record.error_code, "paid_ai_enabled": False,
            "live_reasoning_quality": "UNVERIFIED", "fallback": "Existing deterministic Phase 1 tools remain available."}


def request_proposal(db, user, project_id, request_key, *, config=None, provider=None):
    p, ctx = context_for(db, user, project_id)
    db.execute(update(BusinessProject).where(BusinessProject.id == p.id).values(stage=BusinessProject.stage))
    existing = db.scalar(select(IntelligenceRecord).where(
        IntelligenceRecord.project_id == p.id, IntelligenceRecord.request_key == request_key,
        IntelligenceRecord.user_id == user.id, IntelligenceRecord.tenant_id == user.tenant_id))
    if existing:
        return existing
    config = config or ProviderConfig()
    record = IntelligenceRecord(tenant_id=user.tenant_id, user_id=user.id, project_id=p.id,
                                request_key=request_key, context_hash=sha(canonical(ctx).encode()),
                                context_json=canonical(ctx), provider=config.provider, model=config.model)
    db.add(record); db.flush()
    try:
        result = generate(ctx, record.id, config, provider=provider)
        record.proposal_json = canonical(result.proposal.model_dump())
        record.proposal_hash = sha(record.proposal_json.encode())
        record.status = "VALIDATED"
        record.attempts = result.attempts
        record.usage_json = canonical({"estimated_input_tokens_upper_bound": result.estimated_input_tokens,
            "maximum_output_tokens": result.maximum_output_tokens,
            "estimated_max_cost_microusd": result.estimated_max_cost_microusd,
            "actual_external_cost_microusd": 0, "measurement": "OFFLINE_MOCK_ESTIMATE_NOT_LIVE_USAGE"})
    except ProviderFailure as exc:
        record.status, record.error_code, record.attempts = "FAILED", exc.code, exc.attempts
    audit(db, user, "intelligence_" + record.status.lower(), record.id, 1,
          provider=record.provider, classification=record.classification,
          correlation_id=record.id, error_code=record.error_code)
    db.flush()
    return record
