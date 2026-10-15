"""Tenant-scoped partner applications and operator attestations; no public partner registry."""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PartnerApplication, PartnerPromotion, AuditEvent, User
from ..security import current_user, require_csrf, ensure_not_lockdown
from ..services.official_resources import public_resources
from .growth import platform_owner
from .journey import utc
from .partner_contracts import (
    CATEGORIES, STATUSES, CAPABILITIES, JURISDICTIONS,
    PartnerInput, PartnerUpdate, PartnerReview, PromotionInput, PromotionReview,
)

router = APIRouter(prefix="/api/v2", tags=["B.I.G. private Partner Network"])


def application(db, user, application_id, *, applicant_only=False):
    query = select(PartnerApplication).where(
        PartnerApplication.id == application_id, PartnerApplication.tenant_id == user.tenant_id,
    )
    if applicant_only:
        query = query.where(PartnerApplication.applicant_id == user.id)
    item = db.scalar(query)
    if item is None:
        raise HTTPException(404, "Partner application not found")
    return item


def describe(item, operator=False):
    review = json.loads(item.review_json)
    valid = review.get("valid", False)
    result = {
        "id": item.id, "applicant_id": item.applicant_id, "details": json.loads(item.details_json),
        "status": item.status, "version": item.version, "review_note": item.review_note,
        "verification_status": "MANUAL_REVIEW_RECORDED" if valid else "NOT_VERIFIED",
        "agreement_status": ("ACCEPTED" if review.get("agreement_reference") else
                             "PENDING" if item.status == "AGREEMENT_PENDING" else "NOT_STARTED") if valid else "NOT_STARTED",
        "integration_status": "TEST_EVIDENCE_RECORDED" if valid and review.get("integration_reference") else "NOT_CONNECTED",
        "created_at": utc(item.created_at), "updated_at": utc(item.updated_at),
        "external_actions_enabled": False, "verified_performance": None,
    }
    if operator:
        result["review"] = {
            "evidence": [], "agreement_reference": "", "integration_reference": "", "valid": False,
            **review,
        }
    return result


def audit(db, user, item, action, resource="partner_application"):
    db.add(AuditEvent(
        tenant_id=user.tenant_id, actor_id=user.id, action=f"partner_{action}",
        resource_type=resource, resource_id=item.id,
        details_json=json.dumps({"status": item.status, "version": item.version}),
    ))


def change(db, user, item, expected, values, action, resource="partner_application"):
    ensure_not_lockdown(db, user)
    model = type(item)
    changed = db.execute(update(model).where(
        model.id == item.id, model.tenant_id == user.tenant_id, model.version == expected,
    ).values(**values, version=expected + 1, updated_at=datetime.now(timezone.utc))
      .execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Record changed. Reload and review before retrying.")
    db.refresh(item)
    if model is PartnerApplication and action in {"application_updated", "suspend", "reject", "reopen"}:
        invalidated = db.scalars(update(PartnerPromotion).where(
            PartnerPromotion.tenant_id == user.tenant_id, PartnerPromotion.partner_id == item.id,
            PartnerPromotion.status == "APPROVED",
        ).values(status="DRAFT", version=PartnerPromotion.version + 1,
                 updated_at=datetime.now(timezone.utc)).returning(PartnerPromotion.id)).all()
        for promotion_id in invalidated:
            promotion = db.get(PartnerPromotion, promotion_id)
            db.refresh(promotion)
            audit(db, user, promotion, "promotion_approval_invalidated", "partner_promotion")
    audit(db, user, item, action, resource)
    db.commit()
    db.refresh(item)


@router.get("/partners/catalog")
def catalog():
    return {
        "categories": [{"id": key, "title": name} for key, name in CATEGORIES],
        "statuses": STATUSES, "capabilities": CAPABILITIES,
        "limits": {"business_name": 160, "contact_name": 160, "text": 2000, "coverage": 51},
        "official_resources": [
            {**item, "connection_type": "OFFICIAL_PUBLIC_INFORMATION", "filing_enabled": False,
             "manual_verification_required": True} for item in public_resources()
        ],
        "connection_types": ["OFFICIAL_PUBLIC_INFORMATION", "VERIFIED_API_CONNECTION",
                             "RESTRICTED_PARTNER_API", "AUTHORIZED_FILING_CAPABILITY",
                             "MANUAL_VERIFICATION_REQUIRED"],
        "jurisdictions": [
            {"code": code, "name": name, "reference_url": "https://www.usa.gov/states-and-territories",
             "connection_type": "OFFICIAL_PUBLIC_INFORMATION", "manual_verification_required": True,
             "filing_enabled": False} for code, name in JURISDICTIONS
        ],
        "local_agencies": {"status": "MANUAL_VERIFICATION_REQUIRED", "coverage_verified": False},
        "notice": "References only, not government endorsement, verified APIs or filing coverage.",
    }


@router.get("/partners/applications")
def list_applications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(PartnerApplication).where(
        PartnerApplication.tenant_id == user.tenant_id, PartnerApplication.applicant_id == user.id,
    ).order_by(PartnerApplication.created_at.desc())).all()
    return {"applications": [describe(item) for item in rows]}


@router.post("/partners/applications")
def apply(payload: PartnerInput, user: User = Depends(current_user),
          db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    item = PartnerApplication(tenant_id=user.tenant_id, applicant_id=user.id,
                              details_json=json.dumps(payload.model_dump(mode="json")))
    db.add(item); db.flush()
    audit(db, user, item, "application_submitted")
    db.commit(); db.refresh(item)
    return describe(item)


@router.patch("/partners/applications/{application_id}")
def edit(application_id: str, payload: PartnerUpdate, user: User = Depends(current_user),
         db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = application(db, user, application_id, applicant_only=True)
    if item.status in ("SUSPENDED", "REJECTED"):
        raise HTTPException(409, "An operator must reopen this application before editing.")
    review = json.loads(item.review_json)
    review["valid"] = False  # Keep historical evidence, invalidate the current approval.
    review.pop("agreement_reference", None)
    review.pop("integration_reference", None)
    change(db, user, item, payload.expected_version, {
        "details_json": json.dumps(payload.model_dump(mode="json", exclude={"expected_version"})),
        "status": "APPLICATION", "review_json": json.dumps(review), "review_note": "",
    }, "application_updated")
    return describe(item)


@router.get("/operator/partners")
def operator_list(user: User = Depends(platform_owner), db: Session = Depends(get_db)):
    rows = db.scalars(select(PartnerApplication).where(
        PartnerApplication.tenant_id == user.tenant_id,
    ).order_by(PartnerApplication.created_at.desc())).all()
    return {"applications": [describe(item, True) for item in rows], "capabilities": CAPABILITIES}


@router.post("/operator/partners/{application_id}/review")
def review(application_id: str, payload: PartnerReview, user: User = Depends(platform_owner),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = application(db, user, application_id)
    ensure_not_lockdown(db, user)
    data = json.loads(item.review_json)
    action = payload.action
    if action == "activate":
        raise HTTPException(409, "Live partner activation is not authorized in this foundation.")
    transitions = {
        "begin_review": ({"APPLICATION"}, "UNDER_REVIEW"),
        "request_information": ({"UNDER_REVIEW", "VERIFICATION_REQUIRED"}, "VERIFICATION_REQUIRED"),
        "verify": ({"UNDER_REVIEW", "VERIFICATION_REQUIRED"}, "VERIFIED"),
        "await_agreement": ({"VERIFIED"}, "AGREEMENT_PENDING"),
        "record_agreement": ({"AGREEMENT_PENDING"}, "AGREEMENT_PENDING"),
        "approve": ({"AGREEMENT_PENDING"}, "APPROVED"),
        "begin_integration": ({"APPROVED"}, "INTEGRATION_TESTING"),
        "record_integration": ({"INTEGRATION_TESTING"}, "INTEGRATION_TESTING"),
        "suspend": (set(STATUSES) - {"REJECTED", "SUSPENDED"}, "SUSPENDED"),
        "reject": (set(STATUSES) - {"REJECTED", "SUSPENDED", "ACTIVE"}, "REJECTED"),
        "reopen": ({"REJECTED", "SUSPENDED"}, "UNDER_REVIEW"),
    }
    allowed, next_state = transitions[action]
    if item.status not in allowed:
        raise HTTPException(409, "This transition is not allowed from the current status.")
    if action in {"request_information", "reject", "suspend"} and len(payload.note) < 5:
        raise HTTPException(422, "Explain the information request or review decision.")
    if action in {"verify", "record_agreement", "record_integration"} and len(payload.reference) < 5:
        raise HTTPException(422, "A reviewed evidence reference is required. Do not enter credentials.")
    if action == "verify":
        data["valid"] = True
    if action in {"verify", "record_agreement", "record_integration"}:
        evidence = data.setdefault("evidence", [])
        if len(evidence) >= 100:
            raise HTTPException(409, "Evidence history limit reached; operator review required.")
        evidence.append({"kind": action, "reference": payload.reference, "note": payload.note,
                         "actor_id": user.id, "recorded_at": datetime.now(timezone.utc).isoformat()})
    if action == "record_agreement":
        data["agreement_reference"] = payload.reference
    if action == "record_integration":
        data["integration_reference"] = payload.reference
    if action == "approve" and not (data.get("valid") and data.get("agreement_reference")):
        raise HTTPException(409, "Recorded verification and an accepted agreement are required.")
    if action in {"suspend", "reject", "reopen"}:
        data["valid"] = False
        data.pop("agreement_reference", None); data.pop("integration_reference", None)
    change(db, user, item, payload.expected_version,
           {"status": next_state, "review_json": json.dumps(data), "review_note": payload.note}, action)
    return describe(item, True)


def history(db, user, item):
    rows = db.scalars(select(AuditEvent).where(
        AuditEvent.tenant_id == user.tenant_id, AuditEvent.resource_type == "partner_application",
        AuditEvent.resource_id == item.id,
    ).order_by(AuditEvent.created_at)).all()
    return {"events": [{"action": row.action, "actor_id": row.actor_id, "created_at": utc(row.created_at),
                        "details": json.loads(row.details_json)} for row in rows]}


@router.get("/partners/applications/{application_id}/history")
def applicant_history(application_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return history(db, user, application(db, user, application_id, applicant_only=True))


@router.get("/operator/partners/{application_id}/history")
def operator_history(application_id: str, user: User = Depends(platform_owner), db: Session = Depends(get_db)):
    return history(db, user, application(db, user, application_id))
