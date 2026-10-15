"""Saved, explicitly consented offline consultation. Live AI is never invoked."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AIConsultation, AuditEvent, OnboardingJourney, User
from ..security import current_user, ensure_not_lockdown, require_csrf
from ..services.consultation_engine import (
    MAX_TURNS, Recommendation, get_consultation_provider,
)
from ..services.official_resources import public_resources
from .journey import owned, utc, QUESTIONS
from .consultation_privacy import privacy_state

router = APIRouter(prefix="/api/v2/journeys", tags=["B.I.G. consultation foundation"])


class ConsultationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent: Literal[True]
    expected_version: int = Field(ge=0, strict=True)
    journey_version: int = Field(ge=1, strict=True)
    privacy_version: int = Field(default=0, ge=0, strict=True)
    message: str = Field(min_length=5, max_length=1200)

    @field_validator("message", mode="before")
    @classmethod
    def clean(cls, value):
        return value.strip() if isinstance(value, str) else value


def find(db, user, journey_id):
    return db.scalar(select(AIConsultation).where(
        AIConsultation.journey_id == journey_id, AIConsultation.user_id == user.id,
        AIConsultation.tenant_id == user.tenant_id,
    ))


def describe(item, journey):
    return {
        "id": item.id, "version": item.version, "journey_version": item.journey_version,
        "language": item.language, "detail_mode": item.detail_mode, "mode": "SIMULATION",
        "turns": json.loads(item.turns_json),
        "context_stale": item.journey_version != journey.version,
        "cost": {"actual_cents": 0, "live_authorized": False},
        "consent_at": utc(item.consent_at), "updated_at": utc(item.updated_at),
    }


@router.get("/{journey_id}/consultation")
def get(journey_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    journey = owned(db, user, journey_id)
    item = find(db, user, journey_id)
    return {
        "consultation": describe(item, journey) if item else None,
        "availability": {"mode": "SIMULATION_ONLY", "live_enabled": False,
                         "max_turns": MAX_TURNS, "external_actions_enabled": False},
        "resources": public_resources(journey.language),
        "privacy": privacy_state(db, user, journey_id),
    }


@router.post("/{journey_id}/consultation")
def send(journey_id: str, payload: ConsultationRequest, user: User = Depends(current_user),
         db: Session = Depends(get_db), _: bool = Depends(require_csrf),
         provider=Depends(get_consultation_provider)):
    ensure_not_lockdown(db, user)
    journey = owned(db, user, journey_id)
    privacy = privacy_state(db, user, journey_id)
    if privacy["status"] in ("REVOKED", "DELETED") or privacy["version"] != payload.privacy_version:
        raise HTTPException(409, "Consultation consent is withdrawn or changed. Review privacy controls before continuing.")
    facts = json.loads(journey.answers_json)
    if not all(facts.get(key) for key in QUESTIONS):
        raise HTTPException(409, "Finish and save intake before consulting")
    if journey.version != payload.journey_version:
        raise HTTPException(409, "Business context changed. Reload before continuing.")
    item = find(db, user, journey_id)
    if payload.expected_version != (item.version if item else 0):
        raise HTTPException(409, "Consultation changed. Refresh and review before retrying.")
    turns = json.loads(item.turns_json) if item else []
    if len(turns) >= MAX_TURNS:
        raise HTTPException(429, "Simulation turn limit reached. No paid usage is authorized.")
    try:
        result = provider.recommend(
            context={"answers": facts, "stage": journey.stage,
                     "language": journey.language, "detail_mode": journey.detail_mode},
            message=payload.message, turn=len(turns),
        )
        # Validate even injected implementations. Provider-supplied URLs/status fields are forbidden.
        recommendation = Recommendation.model_validate(
            result.model_dump() if isinstance(result, BaseModel) else result,
        )
    except (ValidationError, ValueError, TypeError, KeyError, RuntimeError, TimeoutError):
        raise HTTPException(503, "Consultation unavailable. Your previous progress is unchanged.") from None
    turns.append({"question": payload.message, "answer": recommendation.model_dump()})
    now = datetime.now(timezone.utc)
    # Guard the intake version through commit: a stale consultation must not silently
    # claim to use the latest saved facts. Locking update serializes concurrent intake edits.
    context_guard = db.execute(update(OnboardingJourney).where(
        OnboardingJourney.id == journey.id, OnboardingJourney.user_id == user.id,
        OnboardingJourney.tenant_id == user.tenant_id,
        OnboardingJourney.version == payload.journey_version,
    ).values(version=payload.journey_version).execution_options(synchronize_session=False))
    if context_guard.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Business context changed. Reload before continuing.")
    # Serialize privacy decisions and saves on the same journey lock. A delayed
    # save must not restore content after withdrawal, deletion, or later re-consent.
    current_privacy = privacy_state(db, user, journey_id)
    if current_privacy != privacy:
        db.rollback()
        raise HTTPException(409, "Consultation privacy changed. Reload before continuing.")
    if item:
        changed = db.execute(update(AIConsultation).where(
            AIConsultation.id == item.id, AIConsultation.user_id == user.id,
            AIConsultation.tenant_id == user.tenant_id,
            AIConsultation.version == payload.expected_version,
        ).values(turns_json=json.dumps(turns), version=item.version + 1,
                 journey_version=journey.version, language=journey.language,
                 detail_mode=journey.detail_mode, updated_at=now)
          .execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Consultation changed. Refresh before retrying.")
    else:
        item = AIConsultation(
            tenant_id=user.tenant_id, user_id=user.id, journey_id=journey.id,
            journey_version=journey.version, language=journey.language,
            detail_mode=journey.detail_mode, turns_json=json.dumps(turns),
        )
        db.add(item)
    try:
        db.flush()
        db.add(AuditEvent(
            tenant_id=user.tenant_id, actor_id=user.id, action="consultation_simulated",
            resource_type="ai_consultation", resource_id=item.id,
            details_json=json.dumps({"consent": True, "mode": "SIMULATION",
                                     "turn_count": len(turns), "actual_cents": 0}),
        ))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Consultation started in another tab. Refresh before retrying.") from None
    db.refresh(item)
    return describe(item, journey)
