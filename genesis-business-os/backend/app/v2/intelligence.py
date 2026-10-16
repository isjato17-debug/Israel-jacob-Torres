"""Private mock-intelligence preview and guarded handoff into the Phase 1 authority."""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, IntelligenceRecord
from ..security import current_user, require_csrf, ensure_not_lockdown
from ..services import intelligence as service, business_orchestrator as engine
from ..services.document_engine import canonical
from ..services.test_signing import sha
from ..services.intelligence_provider import validate_proposal, ProviderFailure
from ..services.project_execution import advance
from .documents import owned, Strict, audit

router = APIRouter(prefix="/api/v2/projects/{project_id}/intelligence", tags=["Private intelligence"])


class ProposalRequest(Strict):
    request_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{16,80}$")


def scoped_record(db, user, project_id, record_id):
    owned(db, user, project_id)
    record = db.scalar(select(IntelligenceRecord).where(
        IntelligenceRecord.id == record_id, IntelligenceRecord.project_id == project_id,
        IntelligenceRecord.user_id == user.id, IntelligenceRecord.tenant_id == user.tenant_id))
    if not record:
        raise HTTPException(404, "Proposal not found")
    return record


@router.get("")
def get(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned(db, user, project_id)
    records = db.scalars(select(IntelligenceRecord).where(
        IntelligenceRecord.project_id == project_id, IntelligenceRecord.user_id == user.id,
        IntelligenceRecord.tenant_id == user.tenant_id).order_by(IntelligenceRecord.created_at.desc()).limit(20))
    return {"paid_ai_enabled": False, "external_spending_authorized_microusd": 0,
            "classification": "MOCK_TEST_NOT_GENUINE_AI", "live_reasoning_quality": "UNVERIFIED",
            "records": [service.serialize(r) for r in records]}


@router.post("/proposals")
def propose(project_id: str, data: ProposalRequest, user: User = Depends(current_user),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    try:
        record = service.request_proposal(db, user, project_id, data.request_key)
        db.commit()
    except (OperationalError, IntegrityError):
        db.rollback()
        raise HTTPException(409, "Request is busy or duplicated; reload saved proposal history.") from None
    return service.serialize(record)


@router.post("/proposals/{record_id}/apply")
def apply(project_id: str, record_id: str, user: User = Depends(current_user),
          db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    record = scoped_record(db, user, project_id, record_id)
    p, ctx = service.context_for(db, user, project_id)
    if not service.serialize(record)["integrity_verified"]:
        raise HTTPException(409, "Proposal integrity failed; existing execution is unchanged")
    if record.context_hash != sha(canonical(ctx).encode()) or record.context_hash != sha(record.context_json.encode()):
        raise HTTPException(409, "Saved context changed. Generate a fresh proposal; no approval transfers.")
    if record.status == "APPLIED":
        return service.serialize(record)
    if record.status != "VALIDATED":
        raise HTTPException(409, "Only a validated proposal can be applied")
    try:
        proposal = validate_proposal(record.proposal_json, ctx)
    except ProviderFailure:
        raise HTTPException(409, "Untrusted proposal rejected; no task was executed") from None
    nodes = engine.rows(db, p)
    if any(task.tool not in nodes for task in proposal.tasks):
        raise HTTPException(409, "Initialize the existing project roadmap before applying a proposal")
    # advance holds the same project lock and performs server-owned capability/dependency checks.
    # It does not consume model-supplied permissions, dependencies, receipts or status claims.
    try:
        advance(db, user, p)
        # A concurrent retry must not duplicate handoff receipts.
        db.refresh(record)
        if record.status != "APPLIED":
            for task in proposal.tasks:
                action, _ = nodes[task.tool]
                engine.evidence(db, user, p, action, "validated_proposal",
                                "Mock proposal accepted as task data, not permission or execution evidence",
                                {"proposal_id": record.id, "proposal_hash": record.proposal_hash,
                                 "classification": record.classification})
            record.status = "APPLIED"
            audit(db, user, "intelligence_proposal_applied", record.id, 1)
        db.commit()
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "Concurrent handoff; reload saved state before retrying") from None
    return service.serialize(record)
