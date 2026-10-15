"""Private operator planning. No channel publishing, spending or simulated metrics."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AuditEvent, GrowthCampaign, User
from ..security import current_user, ensure_not_lockdown, require_csrf

router = APIRouter(prefix="/api/v2/operator", tags=["Private Genesis owner"])


def is_platform_owner(user):
    allowed = {value.strip() for value in settings.platform_owner_user_ids.split(",") if value.strip()}
    return user.id in allowed and user.role in {"owner", "admin"}


def platform_owner(user: User = Depends(current_user)):
    if not is_platform_owner(user):
        raise HTTPException(403, "Platform-owner access required. A customer business-owner role does not grant this access.")
    return user


class CampaignInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=160)
    objective: str = Field(min_length=5, max_length=1200)
    audience: str = Field(min_length=3, max_length=500)
    channel: Literal["website", "email", "social", "referral"]
    content: str = Field(default="", max_length=6000)
    planned_budget_cents: int = Field(default=0, ge=0, le=100_000_000, strict=True)

    @field_validator("title", "objective", "audience", "content", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class CampaignUpdate(CampaignInput):
    expected_version: int = Field(ge=1)


class ReviewAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["request_review", "approve", "pause", "archive", "reopen"]
    expected_version: int = Field(ge=1)
    confirm: bool = False


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def describe(item):
    return {
        "id": item.id, "title": item.title, "objective": item.objective,
        "audience": item.audience, "channel": item.channel, "content": item.content,
        "planned_budget_cents": item.planned_budget_cents, "currency": "USD",
        "status": item.status, "version": item.version,
        "approved_at": utc(item.approved_at) if item.approved_at else None,
        "created_at": utc(item.created_at), "updated_at": utc(item.updated_at),
        "publishing_enabled": False, "spending_authorized": False,
        "verified_performance": None,
    }


def owned(db, user, campaign_id):
    item = db.scalar(select(GrowthCampaign).where(
        GrowthCampaign.id == campaign_id, GrowthCampaign.tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(404, "Campaign not found")
    return item


def audit(db, user, item, action):
    db.add(AuditEvent(
        tenant_id=user.tenant_id, actor_id=user.id, action=f"growth_{action}",
        resource_type="growth_campaign", resource_id=item.id,
        details_json=json.dumps({"status": item.status, "version": item.version}),
    ))


def save(db, user, item, expected_version, values, action):
    ensure_not_lockdown(db, user)
    if item.version != expected_version:
        raise HTTPException(409, "Campaign changed in another session. Reload before saving.")
    result = db.execute(update(GrowthCampaign).where(
        GrowthCampaign.id == item.id, GrowthCampaign.tenant_id == user.tenant_id,
        GrowthCampaign.version == expected_version,
    ).values(**values, version=expected_version + 1, updated_at=datetime.now(timezone.utc))
      .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Campaign changed in another session. Reload before saving.")
    db.refresh(item)
    audit(db, user, item, action)
    db.commit()
    db.refresh(item)
    return describe(item)


@router.get("/access")
def access(user: User = Depends(current_user)):
    return {
        "owner_access": is_platform_owner(user), "account_id": user.id,
        "configuration_required": not bool(settings.platform_owner_user_ids.strip()),
        "publishing_enabled": False, "spending_enabled": False,
    }


@router.get("/campaigns")
def campaigns(user: User = Depends(platform_owner), db: Session = Depends(get_db)):
    rows = db.scalars(select(GrowthCampaign).where(
        GrowthCampaign.tenant_id == user.tenant_id,
    ).order_by(GrowthCampaign.updated_at.desc())).all()
    return {
        "campaigns": [describe(row) for row in rows],
        "overview": {
            "campaign_count": len(rows),
            "planned_budget_cents": sum(row.planned_budget_cents for row in rows if row.status != "ARCHIVED"),
            "currency": "USD", "verified_performance": None,
        },
        "capabilities": {"planning": True, "internal_review": True, "ai_generation": False,
                         "publishing": False, "spending": False, "connected_analytics": False},
        "notice": "Planning and internal review only. Budgets do not authorize spending. No verified marketing results are connected.",
    }


@router.post("/campaigns")
def create(payload: CampaignInput, user: User = Depends(platform_owner),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    item = GrowthCampaign(tenant_id=user.tenant_id, creator_id=user.id, **payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, user, item, "created")
    db.commit()
    db.refresh(item)
    return describe(item)


@router.put("/campaigns/{campaign_id}")
def edit(campaign_id: str, payload: CampaignUpdate, user: User = Depends(platform_owner),
         db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned(db, user, campaign_id)
    if item.status == "ARCHIVED":
        raise HTTPException(409, "Reopen the archived campaign before editing.")
    values = payload.model_dump(exclude={"expected_version"})
    values.update(status="DRAFT", approved_by=None, approved_at=None)
    return save(db, user, item, payload.expected_version, values, "edited")


@router.post("/campaigns/{campaign_id}/review")
def review(campaign_id: str, payload: ReviewAction, user: User = Depends(platform_owner),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned(db, user, campaign_id)
    transitions = {
        "request_review": ({"DRAFT", "PAUSED"}, "IN_REVIEW"),
        "approve": ({"IN_REVIEW"}, "APPROVED"),
        "pause": ({"IN_REVIEW", "APPROVED"}, "PAUSED"),
        "archive": ({"DRAFT", "IN_REVIEW", "APPROVED", "PAUSED"}, "ARCHIVED"),
        "reopen": ({"ARCHIVED"}, "DRAFT"),
    }
    allowed, target = transitions[payload.action]
    if item.status not in allowed:
        raise HTTPException(409, "That review action is not allowed from the current status.")
    if payload.action == "request_review" and len(item.content.strip()) < 10:
        raise HTTPException(422, "Write at least 10 characters of original draft content before review.")
    if payload.action == "approve" and not payload.confirm:
        raise HTTPException(422, "Explicitly confirm internal content approval. This does not authorize publishing or spending.")
    values = {
        "status": target, "approved_by": user.id if target == "APPROVED" else None,
        "approved_at": datetime.now(timezone.utc) if target == "APPROVED" else None,
    }
    return save(db, user, item, payload.expected_version, values, payload.action)
