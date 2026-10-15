"""Account-bound, consented intake. No external executions or completion claims."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditEvent, Business, OnboardingJourney, User
from ..security import current_user, ensure_not_lockdown, require_csrf
from .catalog import STATES, ENTITY_TYPES, OWNERSHIP_TYPES
from .router import Intake, plan

router = APIRouter(prefix="/api/v2/journeys", tags=["Saved Genesis journeys"])
QUESTIONS = ["state", "entity_type", "ownership_type", "goal"]
WORKFLOW_STATES = ["NOT_STARTED", "PREPARED", "SUBMITTED", "PENDING", "APPROVED", "COMPLETED"]

def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class StartJourney(BaseModel):
    stage: Literal["start", "run", "grow"]
    language: Literal["en", "es"] = "en"
    detail_mode: Literal["simple", "details"] = "simple"
    consent: Literal[True]


class Answer(BaseModel):
    field: Literal["state", "entity_type", "ownership_type", "goal"]
    value: str = Field(min_length=1, max_length=1200)
    expected_version: int = Field(ge=1)


class Preferences(BaseModel):
    language: Literal["en", "es"]
    detail_mode: Literal["simple", "details"]
    expected_version: int = Field(ge=1)


def owned(db, user, journey_id):
    item = db.scalar(select(OnboardingJourney).where(
        OnboardingJourney.id == journey_id,
        OnboardingJourney.tenant_id == user.tenant_id,
        OnboardingJourney.user_id == user.id,
    ))
    if item is None:
        raise HTTPException(404, "Journey not found")
    return item


def describe(item):
    answers = json.loads(item.answers_json)
    next_question = next((key for key in QUESTIONS if not answers.get(key)), None)
    prepared = plan(Intake(stage=item.stage, **answers)) if next_question is None else None
    if prepared:
        prepared["persisted"] = True
        prepared["notice"] = prepared["notice"].replace(
            "This preview does not save your answers.",
            "Your consented answers are saved to your account; services have not been submitted.",
        )
        for step in prepared["steps"]:
            step["workflow_status"] = "NOT_STARTED"
    return {
        "id": item.id, "business_id": item.business_id, "stage": item.stage,
        "answers": answers, "language": item.language, "detail_mode": item.detail_mode,
        "version": item.version, "next_question": next_question,
        "answered_count": len([key for key in QUESTIONS if answers.get(key)]),
        "question_count": len(QUESTIONS),
        "status": "PREPARED" if prepared else "IN_PROGRESS",
        "plan": prepared,
        "data_classification": "USER_PROVIDED_NOT_VERIFIED",
        "consent_at": utc(item.consent_at),
        "updated_at": utc(item.updated_at),
        "cost": {"amount_cents": None, "status": "NOT_QUOTED", "charges_authorized": False},
        "notice": "Prepared is not submitted, approved or completed. No external action is performed.",
    }


def audit(db, user, action, item, details):
    db.add(AuditEvent(
        tenant_id=user.tenant_id, actor_id=user.id, action=action,
        resource_type="onboarding_journey", resource_id=item.id,
        details_json=json.dumps(details),
    ))


@router.get("")
def list_journeys(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(OnboardingJourney).where(
        OnboardingJourney.tenant_id == user.tenant_id,
        OnboardingJourney.user_id == user.id,
    ).order_by(OnboardingJourney.created_at)).all()
    return {"journeys": [describe(row) for row in rows], "workflow_states": WORKFLOW_STATES}


@router.post("")
def start(payload: StartJourney, user: User = Depends(current_user),
          db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    existing = db.scalar(select(OnboardingJourney).where(
        OnboardingJourney.tenant_id == user.tenant_id,
        OnboardingJourney.user_id == user.id,
        OnboardingJourney.stage == payload.stage,
    ))
    if existing:
        return describe(existing)
    previous = db.scalar(select(OnboardingJourney).where(
        OnboardingJourney.tenant_id == user.tenant_id,
        OnboardingJourney.user_id == user.id,
    ).order_by(OnboardingJourney.updated_at.desc()))
    business = db.get(Business, previous.business_id) if previous else db.scalar(
        select(Business).where(Business.tenant_id == user.tenant_id)
        .order_by(Business.created_at, Business.id)
    )
    if business is None or business.tenant_id != user.tenant_id:
        business = Business(tenant_id=user.tenant_id, name="My Business", twin_json="{}")
        db.add(business)
        db.flush()
    item = OnboardingJourney(
        tenant_id=user.tenant_id, user_id=user.id, business_id=business.id,
        stage=payload.stage,
        # Reuse authorized business facts, but ask for a fresh stage-specific goal.
        answers_json=json.dumps({
            key: value for key, value in json.loads(previous.answers_json).items() if key != "goal"
        }) if previous else "{}",
        language=payload.language, detail_mode=payload.detail_mode,
    )
    db.add(item)
    try:
        db.flush()
        audit(db, user, "journey_started", item, {
            "stage": payload.stage, "consent": True, "reused_authorized_answers": bool(previous),
        })
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A journey was created in another tab. Reload to continue.")
    db.refresh(item)
    return describe(item)


def save(db, user, item, expected_version, values, action, details):
    ensure_not_lockdown(db, user)
    result = db.execute(update(OnboardingJourney).where(
        OnboardingJourney.id == item.id,
        OnboardingJourney.tenant_id == user.tenant_id,
        OnboardingJourney.user_id == user.id,
        OnboardingJourney.version == expected_version,
    ).values(**values, version=expected_version + 1, updated_at=datetime.now(timezone.utc))
      .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Progress changed in another tab. Reload before saving again.")
    audit(db, user, action, item, details)
    db.commit()
    db.refresh(item)
    return describe(item)


@router.patch("/{journey_id}/answer")
def answer(journey_id: str, payload: Answer, user: User = Depends(current_user),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned(db, user, journey_id)
    answers = json.loads(item.answers_json)
    field, value = payload.field, payload.value.strip()
    choices = {"state": dict(STATES), "entity_type": ENTITY_TYPES, "ownership_type": OWNERSHIP_TYPES}
    if field in choices and value not in choices[field]:
        raise HTTPException(422, "Choose a valid answer")
    if field == "goal" and not 5 <= len(value) <= 1200:
        raise HTTPException(422, "Describe your goal in 5–1,200 characters")
    next_field = next((key for key in QUESTIONS if not answers.get(key)), None)
    if field not in answers and field != next_field:
        raise HTTPException(422, "Answer the current question first")
    answers[field] = value
    return save(db, user, item, payload.expected_version, {"answers_json": json.dumps(answers)},
                "journey_answer_saved", {"field": field})


@router.patch("/{journey_id}/preferences")
def preferences(journey_id: str, payload: Preferences, user: User = Depends(current_user),
                db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned(db, user, journey_id)
    return save(db, user, item, payload.expected_version,
                {"language": payload.language, "detail_mode": payload.detail_mode},
                "journey_preferences_saved", {"language": payload.language, "detail_mode": payload.detail_mode})
