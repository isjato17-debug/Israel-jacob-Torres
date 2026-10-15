"""Internal co-marketing preparation, never public ads, partner endorsement or revenue."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import PartnerApplication, PartnerPromotion, User
from ..security import require_csrf, ensure_not_lockdown
from .growth import platform_owner
from .partner_contracts import PromotionInput, PromotionReview
from .partners import application, audit, change
from .journey import utc

router = APIRouter(prefix="/api/v2/operator/partner-promotions", tags=["Private partner promotion planning"])


def describe(item):
    return {
        "id": item.id, "partner_id": item.partner_id, "title": item.title, "content": item.content,
        "partner_permission_reference": item.partner_permission_reference,
        "status": item.status, "version": item.version, "attribution_code": item.attribution_code,
        "created_at": utc(item.created_at), "updated_at": utc(item.updated_at),
        "verified_performance": None, "publishing_enabled": False,
        "referral_collection_enabled": False, "commission_authorized": False,
    }


@router.get("")
def list_promotions(user: User = Depends(platform_owner), db: Session = Depends(get_db)):
    rows = db.scalars(select(PartnerPromotion).where(
        PartnerPromotion.tenant_id == user.tenant_id,
    ).order_by(PartnerPromotion.created_at.desc())).all()
    return {"promotions": [describe(item) for item in rows], "external_publishing_enabled": False}


@router.post("")
def prepare(payload: PromotionInput, user: User = Depends(platform_owner),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    application(db, user, payload.partner_id)
    item = PartnerPromotion(tenant_id=user.tenant_id, **payload.model_dump(exclude={"consent"}))
    db.add(item); db.flush()
    audit(db, user, item, "promotion_prepared", "partner_promotion")
    db.commit(); db.refresh(item)
    return describe(item)


@router.post("/{promotion_id}/review")
def review(promotion_id: str, payload: PromotionReview, user: User = Depends(platform_owner),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = db.scalar(select(PartnerPromotion).where(
        PartnerPromotion.id == promotion_id, PartnerPromotion.tenant_id == user.tenant_id,
    ))
    if item is None:
        raise HTTPException(404, "Promotion not found")
    if item.status == "ARCHIVED":
        raise HTTPException(409, "Archived promotion cannot be approved")
    if payload.action == "approve":
        partner = application(db, user, item.partner_id)
        if partner.status not in ("APPROVED", "INTEGRATION_TESTING") or len(item.partner_permission_reference.strip()) < 5:
            raise HTTPException(409, "Partner approval and recorded co-marketing permission are required")
        if item.status != "DRAFT":
            raise HTTPException(409, "Only a draft can be approved")
        # Serialize approval with suspension/applicant edits before committing the plan.
        guarded = db.execute(update(PartnerApplication).where(
            PartnerApplication.id == partner.id, PartnerApplication.tenant_id == user.tenant_id,
            PartnerApplication.version == partner.version,
            PartnerApplication.status.in_(("APPROVED", "INTEGRATION_TESTING")),
        ).values(version=partner.version).execution_options(synchronize_session=False))
        if guarded.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Partner approval changed. Refresh before reviewing promotion.")
    change(db, user, item, payload.expected_version,
           {"status": "APPROVED" if payload.action == "approve" else "ARCHIVED"},
           f"promotion_{payload.action}", "partner_promotion")
    return describe(item)
