"""Customer-private AutoForm continuation of existing projects and consultant engines."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (User, BusinessProject, BusinessIdea, Business, FounderProfile, BusinessPassport,
                      DocumentWorkflow, GeneratedDocument, DocumentApproval, ExecutionTask, AuditEvent)
from ..security import current_user, require_csrf, ensure_not_lockdown
from ..services import document_engine as forms
from ..services.consultant import executive_board, financial_model, industry
from ..services.product_engine import founder_score
from ..services.external_readiness import connection_records, fetch_public_notices
from .journey import utc

router = APIRouter(prefix="/api/v2/projects", tags=["Project AutoForm"])


@router.get("/{project_id}/execution/connections")
def connections(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned(db, user, project_id)
    return {"connections": connection_records(), "external_actions_authorized": False,
            "notice": "Standby is not activation. Free/public reads are separate from filings, signatures, payments and data sharing."}


@router.post("/{project_id}/execution/connections/public-check")
def public_check(project_id: str, user: User = Depends(current_user),
                 db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    owned(db, user, project_id)
    return fetch_public_notices()


def owned(db, user, project_id):
    p = db.scalar(select(BusinessProject).where(BusinessProject.id == project_id,
                  BusinessProject.tenant_id == user.tenant_id, BusinessProject.user_id == user.id))
    if not p:
        raise HTTPException(404, "Project not found")
    return p


def workflow(db, p):
    return db.scalar(select(DocumentWorkflow).where(
        DocumentWorkflow.project_id == p.id, DocumentWorkflow.template_key == forms.TEMPLATE_KEY,
        DocumentWorkflow.tenant_id == p.tenant_id, DocumentWorkflow.user_id == p.user_id))


def passport(db, p):
    return db.scalar(select(BusinessPassport).where(
        BusinessPassport.project_id == p.id, BusinessPassport.tenant_id == p.tenant_id,
        BusinessPassport.user_id == p.user_id))


def audit(db, user, action, resource, version, **extra):
    db.add(AuditEvent(tenant_id=user.tenant_id, actor_id=user.id, action=action,
                     resource_type="autoform", resource_id=resource,
                     details_json=json.dumps({"version": version, **extra})))


def describe_document(db, d):
    source = json.loads(d.source_json)
    if forms.digest(source) != d.content_hash:
        raise HTTPException(409, "Document integrity check failed; review blocked")
    a = db.scalar(select(DocumentApproval).where(DocumentApproval.document_id == d.id))
    return {"id": d.id, "revision": d.revision, "content_hash": d.content_hash,
            "filename": f"cleaning-service-agreement-{d.id}-r{d.revision}.html",
            "created_at": utc(d.created_at), "sections": forms.sections(source),
            "approval": {"approved_at": utc(a.created_at), "purpose": a.purpose} if a else None}


def context(db, user, p):
    idea = db.get(BusinessIdea, p.idea_id)
    facts = json.loads(idea.facts_json)
    business = db.get(Business, p.business_id)
    twin = json.loads(business.twin_json)
    plan = json.loads(p.plan_json)
    prof = db.scalar(select(FounderProfile).where(
        FounderProfile.tenant_id == user.tenant_id, FounderProfile.user_id == user.id))
    saved = passport(db, p)
    w = workflow(db, p)
    docs = db.scalars(select(GeneratedDocument).where(GeneratedDocument.workflow_id == w.id)
                     .order_by(GeneratedDocument.revision.desc())).all() if w else []
    records = [describe_document(db, d) for d in docs]
    supported = industry(facts["industry"] + " " + facts["concept"]) == "cleaning"
    action = ("Arrange an appropriate signature process with both parties. B.I.G. has not signed or sent anything."
              if w and w.status == "READY_FOR_SIGNATURE" else
              "Review the generated document, correct any errors, then explicitly approve this exact revision."
              if w and w.status == "GENERATED" else
              "Complete missing agreement fields and generate the unsigned document."
              if w else "Prepare a Cleaning Service Agreement for your first customer."
              if supported else "No native document template supports this business yet; existing planning tools remain available.")
    return {
        "project_id": p.id, "supported": supported, "template": forms.definition(),
        "passport": {"version": saved.version if saved else 0,
                     "fields": json.loads(saved.fields_json) if saved else {},
                     "classification": "CUSTOMER_AUTHORIZED_NOT_VERIFIED"},
        "assistant": {
            "classification": "DETERMINISTIC_NOT_AI_GENERATED", "live_ai_connected": False,
            "summary": f"Your ${p.budget_cents / 100:,.2f} project uses the saved {plan['name']} plan. "
                       "This continuation reuses the existing financial, Digital Twin and Executive Board engines.",
            "next_action": action,
            "reasons": [
                f"Selected-plan funding gap: ${plan['funding_gap_cents'] / 100:,.2f}; agreement preparation does not resolve or spend it.",
                "Define client, scope, price and responsibilities before customer work.",
                "Business Passport reuse requires your explicit permission; no identity verification is claimed.",
            ],
            "financials": financial_model(twin), "board": executive_board("What should I do next?", twin, []),
            "founder_dna": {"status": "SAVED_CUSTOMER_PROFILE" if prof else "NOT_PROVIDED_NO_SCORE_INVENTED",
                            "assessment": founder_score(json.loads(prof.profile_json)) if prof else None},
        },
        "workflow": {"id": w.id, "version": w.version, "status": w.status,
                     "fields": json.loads(w.fields_json), "missing": forms.missing(json.loads(w.fields_json)),
                     "documents": records, "latest_document": records[0] if records else None} if w else None,
    }


def finish(db, user, p):
    try:
        db.flush()
        from ..services.business_orchestrator import reconcile
        reconcile(db, user, p)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Workflow changed. Reload and review; nothing was replayed.") from None
    return context(db, user, p)


def change(db, w, expected, **values):
    if not w or w.version != expected:
        raise HTTPException(409, "Document workflow changed. Reload before continuing.")
    result = db.execute(update(DocumentWorkflow).where(
        DocumentWorkflow.id == w.id, DocumentWorkflow.version == expected,
    ).values(**values, version=expected + 1, updated_at=datetime.now(timezone.utc))
      .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Document workflow changed. Reload before continuing.")
    db.refresh(w)


def sync_project(db, p, w):
    p.stage = {"DRAFT": "DOCUMENT_DRAFT", "GENERATED": "DOCUMENT_REVIEW",
               "READY_FOR_SIGNATURE": "SIGNATURE_READY"}[w.status]
    task = db.scalar(select(ExecutionTask).where(
        ExecutionTask.tenant_id == p.tenant_id, ExecutionTask.business_id == p.business_id,
        ExecutionTask.kpi == f"document:{w.id}:review"))
    if not task:
        task = ExecutionTask(tenant_id=p.tenant_id, business_id=p.business_id,
                             horizon="today", task="Review Cleaning Service Agreement before signature preparation",
                             budget="0", kpi=f"document:{w.id}:review")
        db.add(task)
    task.status = "done" if w.status == "READY_FOR_SIGNATURE" else "todo"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PassportSave(Strict):
    expected_version: int = Field(ge=0, strict=True)
    consent: Literal[True]
    fields: forms.PassportFields


class Start(Strict):
    template_key: Literal["cleaning_service_agreement"]


class Version(Strict):
    expected_version: int = Field(ge=1, strict=True)


class Draft(Version):
    fields: forms.AgreementFields


class Approval(Version):
    document_id: str = Field(min_length=1, max_length=80)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    confirmed: Literal[True]


@router.get("/{project_id}/execution")
def get(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return context(db, user, owned(db, user, project_id))


@router.put("/{project_id}/execution/passport")
def save_passport(project_id: str, payload: PassportSave, user: User = Depends(current_user),
                  db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    p = owned(db, user, project_id); saved = passport(db, p)
    values = forms.canonical(payload.fields.model_dump())
    if saved:
        changed = db.execute(update(BusinessPassport).where(
            BusinessPassport.id == saved.id, BusinessPassport.version == payload.expected_version,
        ).values(fields_json=values, version=payload.expected_version + 1,
                 consent_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
        if changed.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Passport changed. Reload before saving.")
    elif payload.expected_version == 0:
        db.add(BusinessPassport(project_id=p.id, tenant_id=user.tenant_id,
                               user_id=user.id, fields_json=values))
    else:
        raise HTTPException(409, "Passport changed. Reload before saving.")
    audit(db, user, "passport_saved", p.id, payload.expected_version + 1)
    return finish(db, user, p)


@router.post("/{project_id}/execution/documents")
def start(project_id: str, payload: Start, user: User = Depends(current_user),
          db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    p = owned(db, user, project_id)
    if not context(db, user, p)["supported"]:
        raise HTTPException(422, "Only the cleaning-service agreement template is supported")
    w = workflow(db, p)
    if w:
        return context(db, user, p)
    saved = passport(db, p)
    fields = forms.AgreementFields(**(json.loads(saved.fields_json) if saved else {})).model_dump()
    w = DocumentWorkflow(project_id=p.id, tenant_id=user.tenant_id, user_id=user.id,
                         template_key=payload.template_key, fields_json=forms.canonical(fields))
    db.add(w)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Workflow creation changed. Reload to resume the existing workflow.") from None
    sync_project(db, p, w)
    audit(db, user, "document_workflow_started", w.id, 1,
          passport_version=saved.version if saved else 0)
    return finish(db, user, p)


@router.patch("/{project_id}/execution/document")
def save(project_id: str, payload: Draft, user: User = Depends(current_user),
         db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    p = owned(db, user, project_id); w = workflow(db, p)
    change(db, w, payload.expected_version, fields_json=forms.canonical(payload.fields.model_dump()), status="DRAFT")
    sync_project(db, p, w)
    audit(db, user, "document_fields_saved", w.id, w.version)
    return finish(db, user, p)


@router.post("/{project_id}/execution/generate")
def generate(project_id: str, payload: Version, user: User = Depends(current_user),
             db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    p = owned(db, user, project_id); w = workflow(db, p)
    if not w:
        raise HTTPException(409, "Start the document workflow first")
    fields = forms.AgreementFields(**json.loads(w.fields_json)).model_dump()
    absent = forms.missing(fields)
    if absent:
        raise HTTPException(422, "Complete required fields: " + ", ".join(forms.LABELS[k] for k in absent))
    change(db, w, payload.expected_version, status="GENERATED")
    previous = db.scalars(select(GeneratedDocument).where(GeneratedDocument.workflow_id == w.id)).all()
    facts = json.loads(db.get(BusinessIdea, p.idea_id).facts_json)
    source = {"template_version": forms.TEMPLATE_VERSION, "fields": fields,
              "project_name": p.name, "plan_name": json.loads(p.plan_json)["name"],
              "jurisdiction": facts["jurisdiction"], "prepared_at": datetime.now(timezone.utc).isoformat()}
    db.add(GeneratedDocument(workflow_id=w.id, revision=len(previous) + 1,
                             source_json=forms.canonical(source), content_hash=forms.digest(source)))
    sync_project(db, p, w)
    audit(db, user, "document_generated", w.id, w.version, revision=len(previous) + 1)
    return finish(db, user, p)


@router.post("/{project_id}/execution/approve")
def approve(project_id: str, payload: Approval, user: User = Depends(current_user),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    p = owned(db, user, project_id); w = workflow(db, p)
    d = db.scalar(select(GeneratedDocument).where(GeneratedDocument.workflow_id == w.id)
                  .order_by(GeneratedDocument.revision.desc())) if w else None
    if not d or w.status != "GENERATED" or d.id != payload.document_id or d.content_hash != payload.content_hash:
        raise HTTPException(409, "Review the latest generated document before approving")
    if forms.digest(json.loads(d.source_json)) != d.content_hash:
        raise HTTPException(409, "Document integrity check failed; approval blocked")
    change(db, w, payload.expected_version, status="READY_FOR_SIGNATURE")
    db.add(DocumentApproval(document_id=d.id, user_id=user.id, content_hash=d.content_hash))
    sync_project(db, p, w)
    audit(db, user, "document_approved_for_signature_preparation", w.id, w.version,
          document_id=d.id, content_hash=d.content_hash)
    return finish(db, user, p)


@router.get("/{project_id}/execution/documents/{document_id}/download")
def download(project_id: str, document_id: str, user: User = Depends(current_user),
             db: Session = Depends(get_db)):
    p = owned(db, user, project_id); w = workflow(db, p)
    d = db.scalar(select(GeneratedDocument).where(
        GeneratedDocument.id == document_id, GeneratedDocument.workflow_id == w.id)) if w else None
    if not d:
        raise HTTPException(404, "Document not found")
    source = json.loads(d.source_json)
    if forms.digest(source) != d.content_hash:
        raise HTTPException(409, "Document integrity check failed; download blocked")
    return Response(forms.render(source), media_type="text/html", headers={
        "Content-Disposition": f'attachment; filename="cleaning-service-agreement-{d.id}-r{d.revision}.html"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "X-Document-SHA256": d.content_hash,
    })
