"""Consented private funding preparation; no applications, credit checks or external sharing."""
import json
from datetime import datetime, timezone, date
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, FundingProfile, FundingApplication, BusinessProject, ExecutionTask
from ..security import current_user, require_csrf, ensure_not_lockdown
from ..services import funding as service, business_orchestrator as engine
from ..services.funding_catalog import PROGRAMS
from ..services.document_engine import canonical
from ..services.test_signing import sha
from .documents import owned, Strict, audit

router = APIRouter(prefix="/api/v2/projects/{project_id}/funding", tags=["Private funding and entrepreneur support"])


class Approval(Strict):
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed: Literal[True]


class Tracking(Strict):
    deadline: str | None = None
    reported_outcome: Literal["NOT_SUBMITTED", "USER_REPORTED_SUBMITTED", "USER_REPORTED_DECLINED",
                              "USER_REPORTED_AWARDED", "WITHDRAWN"] = "NOT_SUBMITTED"

    @field_validator("deadline")
    @classmethod
    def valid_date(cls, value):
        if value and date.fromisoformat(value).isoformat() != value:
            raise ValueError("Use YYYY-MM-DD")
        return value


def locked(db,user,project_id):
    ensure_not_lockdown(db,user)
    p = owned(db,user,project_id)
    db.execute(update(BusinessProject).where(BusinessProject.id == p.id).values(stage=BusinessProject.stage))
    return p


def application(db,p,application_id):
    row = db.scalar(select(FundingApplication).where(FundingApplication.id == application_id,
        FundingApplication.project_id == p.id, FundingApplication.user_id == p.user_id,
        FundingApplication.tenant_id == p.tenant_id))
    if not row:
        raise HTTPException(404,"Application preparation not found")
    return row


@router.get("")
def get(project_id: str,user: User=Depends(current_user),db: Session=Depends(get_db)):
    return service.view(db,owned(db,user,project_id))


@router.put("/profile")
def save(project_id: str,data: service.FundingInput,user: User=Depends(current_user),
         db: Session=Depends(get_db),_: bool=Depends(require_csrf)):
    p = locked(db,user,project_id)
    nodes = engine.rows(db,p)
    if not all(key in nodes for key in engine.SPECS):
        raise HTTPException(409,"Initialize the existing Master Orchestrator roadmap before funding preparation")
    old = service.profile_for(db,p)
    if (old.version if old else 0) != data.expected_version:
        raise HTTPException(409,"Funding profile changed; reload before saving")
    payload = canonical(data.model_dump(exclude={"expected_version","consent"}))
    if old:
        old.version += 1; old.profile_json = payload
    else:
        db.add(FundingProfile(project_id=p.id,user_id=user.id,tenant_id=user.tenant_id,profile_json=payload))
    db.flush()
    service.refresh(db,user,p)
    audit(db,user,"funding_profile_saved",p.id,(old.version if old else 1))
    db.commit()
    return service.view(db,p)


@router.post("/affordability")
def quote(project_id: str,data: service.LoanQuote,user: User=Depends(current_user),db: Session=Depends(get_db),
          _: bool=Depends(require_csrf)):
    ensure_not_lockdown(db,user)
    p=locked(db,user,project_id)
    if not service.profile_for(db,p):
        raise HTTPException(409,"Save a consented private funding profile before storing loan scenarios")
    if data.upfront_fee_cents >= data.principal_cents:
        raise HTTPException(422,"Upfront fee must be less than principal")
    result = service.affordability(data,json.loads(p.plan_json)["operating_profit_cents"])
    nodes = engine.rows(db,p)
    action, record = nodes.get("funding:affordability") or engine.create_action(
        db,user,p,"funding:affordability","Compare saved loan affordability scenarios","Deterministic financial model",[])
    from ..services.project_execution import save_output
    save_output(db,user,p,action,record,{"input":data.model_dump(),"result":result})
    audit(db,user,"funding_quote_calculated_not_lender_offer",p.id,1)
    db.commit()
    return result


@router.post("/applications/{application_id}/approve")
def approve(project_id: str,application_id: str,data: Approval,user: User=Depends(current_user),
            db: Session=Depends(get_db),_: bool=Depends(require_csrf)):
    p=locked(db,user,project_id)
    service.refresh(db,user,p)
    row=application(db,p,application_id)
    latest=next(a for a in service.applications(db,p) if a.opportunity_id == row.opportunity_id)
    eligibility=next(o for o in service.view(db,p)["opportunities"] if o["id"] == row.opportunity_id)
    if (latest.id != row.id or row.revision != data.revision or row.content_hash != data.content_hash
        or sha(canonical(json.loads(row.source_json)).encode()) != row.content_hash
        or eligibility["match_status"] in ("INELIGIBLE_PUBLISHED_CRITERION","SOURCE_STALE_REVERIFY_REQUIRED")):
        raise HTTPException(409,"Only the exact current eligible-for-preparation revision may be approved")
    if not row.approved_hash:
        row.approved_hash=row.content_hash; row.approved_at=datetime.now(timezone.utc)
        title=next(o["name"] for o in PROGRAMS if o["id"] == row.opportunity_id)
        for task in db.scalars(select(ExecutionTask).where(ExecutionTask.business_id == p.business_id,
            ExecutionTask.tenant_id == p.tenant_id,ExecutionTask.task == "Review internal funding packet: " + title)):
            task.status="done"
        audit(db,user,"funding_packet_approved_internal_only",row.id,row.revision,content_hash=row.content_hash)
    db.flush(); service.refresh(db,user,p); db.commit()
    return service.view(db,p)


@router.patch("/applications/{application_id}/tracking")
def tracking(project_id: str,application_id: str,data: Tracking,user: User=Depends(current_user),
             db: Session=Depends(get_db),_: bool=Depends(require_csrf)):
    p=locked(db,user,project_id); row=application(db,p,application_id)
    row.deadline=data.deadline; row.reported_outcome=data.reported_outcome
    audit(db,user,"funding_outcome_customer_reported_unverified",row.id,row.revision)
    db.commit();return service.view(db,p)


@router.get("/applications/{application_id}/download")
def download(project_id: str,application_id: str,user: User=Depends(current_user),db: Session=Depends(get_db)):
    p=owned(db,user,project_id); row=application(db,p,application_id)
    if not service.describe_application(row)["integrity_verified"]:
        raise HTTPException(409,"Packet integrity failed")
    return Response(row.source_json,media_type="application/json",
        headers={"Content-Disposition":f'attachment; filename="funding-packet-{row.id}-r{row.revision}.json"',
                 "Cache-Control":"no-store"})
