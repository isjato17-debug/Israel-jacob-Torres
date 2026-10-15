"""Explicit consultation withdrawal and user-directed transcript erasure, not account deletion."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AIConsultation, AuditEvent, ConsultationPrivacy, OnboardingJourney, User
from ..security import current_user, require_csrf, ensure_not_lockdown
from .journey import owned, utc

router = APIRouter(prefix="/api/v2/journeys", tags=["Consultation privacy"])


def privacy_state(db, user, journey_id):
    row = db.scalar(select(ConsultationPrivacy).where(
        ConsultationPrivacy.journey_id == journey_id,
        ConsultationPrivacy.tenant_id == user.tenant_id, ConsultationPrivacy.user_id == user.id,
    ).execution_options(populate_existing=True))
    return {
        "status": row.status if row else "NOT_WITHDRAWN",
        "version": row.version if row else 0,
        "updated_at": utc(row.updated_at) if row else None,
    }


def lock_journey(db, user, journey):
    guard = db.execute(update(OnboardingJourney).where(
        OnboardingJourney.id == journey.id, OnboardingJourney.user_id == user.id,
        OnboardingJourney.tenant_id == user.tenant_id, OnboardingJourney.version == journey.version,
    ).values(version=journey.version).execution_options(synchronize_session=False))
    if guard.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Business context changed. Reload before continuing.")


class PrivacyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["revoke", "delete", "grant"]
    expected_version: int = Field(ge=0, strict=True)
    consultation_version: int = Field(ge=0, strict=True)
    confirmed: Literal[True]


@router.post("/{journey_id}/consultation/privacy")
def decide(journey_id: str, payload: PrivacyDecision, user: User = Depends(current_user),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    journey = owned(db, user, journey_id)
    lock_journey(db, user, journey)
    state = privacy_state(db, user, journey_id)
    item = db.scalar(select(AIConsultation).where(
        AIConsultation.journey_id == journey_id, AIConsultation.user_id == user.id,
        AIConsultation.tenant_id == user.tenant_id,
    ).execution_options(populate_existing=True))
    if state["version"] != payload.expected_version or (item.version if item else 0) != payload.consultation_version:
        db.rollback()
        raise HTTPException(409, "Consultation or privacy choice changed. Reload and review before retrying.")
    status = {"revoke": "REVOKED", "delete": "DELETED", "grant": "GRANTED"}[payload.action]
    now = datetime.now(timezone.utc)
    if item:
        values = {"version": item.version + 1, "updated_at": now}
        if payload.action == "delete":
            values["turns_json"] = "[]"
        changed = db.execute(update(AIConsultation).where(
            AIConsultation.id == item.id, AIConsultation.version == payload.consultation_version,
        ).values(**values).execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Consultation changed. Reload before retrying.")
    if state["version"]:
        db.execute(update(ConsultationPrivacy).where(
            ConsultationPrivacy.journey_id == journey_id,
            ConsultationPrivacy.version == payload.expected_version,
        ).values(status=status, version=payload.expected_version + 1, updated_at=now))
    else:
        db.add(ConsultationPrivacy(
            journey_id=journey_id, user_id=user.id, tenant_id=user.tenant_id, status=status,
        ))
    db.add(AuditEvent(
        tenant_id=user.tenant_id, actor_id=user.id, action=f"consultation_{payload.action}",
        resource_type="consultation_privacy", resource_id=journey_id,
        details_json=json.dumps({"status": status, "version": payload.expected_version + 1}),
    ))
    db.commit()
    return {
        "privacy": privacy_state(db, user, journey_id),
        "notice": "Withdrawal blocks further consultation processing. Deletion clears the saved transcript only; intake, business and financial records remain. Existing backups may retain earlier data pending reviewed retention/restore controls.",
    }
