"""Private orchestration, test signing/submission and human-reviewed public-source changes."""
import json
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import Field, SecretStr
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import (User, DocumentApproval, GeneratedDocument, TestDocumentSignature, TestSubmission,
                      RegulatorySourceRevision, RegulatoryChangeRecord, ExecutionTask, uid)
from ..security import current_user, require_csrf, ensure_not_lockdown, verify_password
from ..services.security_runtime import login_guard, login_failed, login_succeeded
from ..services import business_orchestrator as engine, test_signing as signing
from ..services.document_engine import canonical, digest, PassportFields
from ..services.regulatory_collection import collect_sources
from .documents import owned, Strict, audit

router = APIRouter(prefix="/api/v2/projects/{project_id}/orchestrator", tags=["Business Orchestrator"])


class Version(Strict):
    expected_version: int = Field(ge=1, strict=True)


class Confirm(Strict):
    confirmed: Literal[True]


class Accept(Version, Confirm):
    pass


class Sign(Version):
    document_id: str = Field(max_length=80)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    typed_name: str = Field(min_length=1, max_length=160)
    password: SecretStr
    request_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{16,80}$")
    reviewed: Literal[True]
    consent: Literal[True]
    disclosure_version: Literal["test-sign-v1"]


class Authorize(Accept):
    signature_id: str = Field(max_length=80)
    request_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{16,80}$")
    outcome: Literal["ACCEPTED", "REJECTED", "CORRECTION_REQUIRED"] = "ACCEPTED"


class Review(Accept):
    decision: Literal["REVIEWED", "NOT_APPLICABLE", "NEEDS_PROFESSIONAL_REVIEW"]


def finish(db, user, p, action):
    try:
        db.flush()
        engine.reconcile(db, user, p)
        audit(db, user, action, p.id, 1)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent or duplicate request. Reload; no operation was replayed.") from None
    return engine.view(db, user, p)


def writable(db, user, project_id):
    ensure_not_lockdown(db, user)
    return owned(db, user, project_id)


@router.get("")
def get(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return engine.view(db, user, owned(db, user, project_id))


@router.post("/start")
def start(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db),
          _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    if not engine.rows(db, p):
        for key, (title, subsystem, deps) in engine.SPECS.items():
            a, r = engine.create_action(db, user, p, key, title, subsystem, deps)
            engine.evidence(db, user, p, a, "created", "Project action initialized; no external action")
    return finish(db, user, p, "orchestrator_initialized")


@router.post("/strategy")
def accept_strategy(project_id: str, data: Accept, user: User = Depends(current_user),
                    db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    a, r = engine.checked_node(db, p, "strategy", data.expected_version, {"AWAITING_CUSTOMER_APPROVAL"})
    engine.set_state(a, r, "COMPLETED_VERIFIED")
    engine.evidence(db, user, p, a, "selected_plan_review", "Customer reviewed alternatives and retained the saved selected plan",
                    {"selected": json.loads(p.plan_json)["key"]})
    return finish(db, user, p, "strategy_reviewed")


def approved_document(db, p, document_id=None, content_hash=None):
    w, d = engine.document_state(db, p)
    approval = db.scalar(select(DocumentApproval).where(DocumentApproval.document_id == d.id)) if d else None
    if (not w or w.status != "READY_FOR_SIGNATURE" or not d or not approval
        or approval.user_id != p.user_id or approval.content_hash != d.content_hash
        or (document_id is not None and d.id != document_id)
        or (content_hash is not None and d.content_hash != content_hash)
        or digest(json.loads(d.source_json)) != d.content_hash):
        raise HTTPException(409, "Review and approve the exact current revision first")
    return d


@router.post("/sign")
def sign(project_id: str, data: Sign, user: User = Depends(current_user), db: Session = Depends(get_db),
         _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    d = approved_document(db, p, data.document_id, data.content_hash)
    name = PassportFields(representative_name=data.typed_name).representative_name
    if not name or name != json.loads(d.source_json)["fields"]["representative_name"]:
        raise HTTPException(422, "Type the exact provider representative name from the approved document")
    identity = "test-sign:" + user.id
    login_guard(identity)
    if len(data.password.get_secret_value()) > 1024 or not verify_password(data.password.get_secret_value(), user.password_hash):
        login_failed(identity)
        raise HTTPException(403, "Reauthentication failed")
    login_succeeded(identity)
    prior = db.scalar(select(TestDocumentSignature).where(TestDocumentSignature.project_id == p.id,
                      TestDocumentSignature.request_key == data.request_key))
    if prior:
        envelope = json.loads(prior.envelope_json)
        if prior.document_id != d.id or prior.revoked_at or envelope["typed_name"] != name or not signing.verify(prior, d):
            raise HTTPException(409, "Request key belongs to a different or withdrawn signature")
        return engine.view(db, user, p)
    a, r = engine.checked_node(db, p, "sign", data.expected_version, {"AWAITING_CUSTOMER_APPROVAL"})
    envelope = {"signature_id": uid(), "project_id": p.id, "document_id": d.id, "document_hash": d.content_hash,
                "user_id": user.id, "typed_name": name, "signed_at": datetime.now(timezone.utc).isoformat(),
                "purpose": "TEST_ONLY_NOT_A_LEGALLY_EXECUTED_CONTRACT", "auth": "PASSWORD_REAUTHENTICATED",
                "disclosure_version": signing.DISCLOSURE_VERSION, "disclosure": signing.DISCLOSURE,
                "reviewed": True, "consent": True, "renderer_version": 1}
    artifact_hash = signing.sha(signing.render_signed(json.loads(d.source_json), envelope))
    record = TestDocumentSignature(id=envelope["signature_id"], project_id=p.id, document_id=d.id, user_id=user.id,
        request_key=data.request_key, envelope_json=canonical(envelope), artifact_hash=artifact_hash,
        audit_mac=signing.mac(envelope, artifact_hash))
    db.add(record); a.attempts += 1
    engine.evidence(db, user, p, a, "test_signature", "Test provider signed exact revision after disclosures and password reauthentication",
                    {"signature_id": record.id, "artifact_hash": artifact_hash}, synthetic=True)
    return finish(db, user, p, "test_signature_created")


def signature_for(db, p, signature_id):
    s = db.scalar(select(TestDocumentSignature).where(TestDocumentSignature.id == signature_id,
                                                    TestDocumentSignature.project_id == p.id))
    if not s:
        raise HTTPException(404, "Test signature not found")
    return s


@router.get("/signatures/{signature_id}/download")
def download(project_id: str, signature_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = owned(db, user, project_id); s = signature_for(db, p, signature_id)
    d = db.get(GeneratedDocument, s.document_id)
    if not signing.verify(s, d):
        raise HTTPException(409, "Test artifact integrity check failed")
    return Response(signing.render_signed(json.loads(d.source_json), json.loads(s.envelope_json)), media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="TEST-agreement-{s.id}.html"', "Cache-Control": "no-store",
                 "X-Content-Type-Options": "nosniff", "X-Document-SHA256": s.artifact_hash,
                 "X-Test-Signature-Status": "REVOKED" if s.revoked_at else "TEST_ONLY"})


@router.post("/signatures/{signature_id}/withdraw")
def withdraw(project_id: str, signature_id: str, data: Confirm, user: User = Depends(current_user),
             db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id); s = signature_for(db, p, signature_id)
    if not s.revoked_at:
        s.revoked_at = datetime.now(timezone.utc)
        a, r = engine.rows(db, p)["sign"]
        engine.evidence(db, user, p, a, "consent_withdrawn", "Test consent withdrawn; immutable historical copy retained",
                        {"signature_id": s.id}, synthetic=True)
    return finish(db, user, p, "test_consent_withdrawn")


def package_current(db, p, submission):
    d = approved_document(db, p)
    sig = signature_for(db, p, submission.signature_id)
    if sig.revoked_at or sig.document_id != d.id or not signing.verify(sig, d) or submission.package_hash != sig.artifact_hash:
        raise HTTPException(409, "Test package is no longer authorized for the current document")
    return sig


@router.post("/submission/authorize")
def authorize(project_id: str, data: Authorize, user: User = Depends(current_user),
              db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    old = db.scalar(select(TestSubmission).where(TestSubmission.project_id == p.id, TestSubmission.request_key == data.request_key))
    if old:
        if old.signature_id != data.signature_id or old.outcome != data.outcome:
            raise HTTPException(409, "Request key is already bound to another package")
        package_current(db, p, old)
        return engine.view(db, user, p)
    s = signature_for(db, p, data.signature_id)
    d = approved_document(db, p)
    if s.revoked_at or s.document_id != d.id or not signing.verify(s, d):
        raise HTTPException(409, "A valid current TEST signature is required")
    a, r = engine.checked_node(db, p, "submit", data.expected_version,
                               {"AWAITING_CUSTOMER_APPROVAL", "FAILED", "CORRECTION_REQUIRED", "CANCELLED"})
    db.add(TestSubmission(project_id=p.id, signature_id=s.id, request_key=data.request_key,
                          outcome=data.outcome, package_hash=s.artifact_hash))
    engine.set_state(a, r, "AUTHORIZED")
    engine.evidence(db, user, p, a, "test_package_authorized", "Customer authorized local TEST adapter only",
                    {"package_hash": s.artifact_hash, "outcome": data.outcome}, synthetic=True)
    return finish(db, user, p, "test_submission_authorized")


def latest_submission(db, p):
    t = db.scalar(select(TestSubmission).where(TestSubmission.project_id == p.id)
                  .order_by(TestSubmission.created_at.desc()))
    if not t:
        raise HTTPException(409, "Authorize a test package first")
    return t


@router.post("/submission/dispatch")
def dispatch(project_id: str, data: Version, user: User = Depends(current_user), db: Session = Depends(get_db),
             _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id); t = latest_submission(db, p); package_current(db, p, t)
    if t.status in ("AWAITING_EXTERNAL_RESULT", "SIMULATED_ACCEPTED", "SIMULATED_REJECTED", "SIMULATED_CORRECTION_REQUIRED"):
        return engine.view(db, user, p)
    a, r = engine.checked_node(db, p, "submit", data.expected_version, {"AUTHORIZED"})
    if t.status != "AUTHORIZED":
        raise HTTPException(409, "Test dispatch is not authorized")
    engine.set_state(a, r, "IN_PROGRESS")
    engine.evidence(db, user, p, a, "test_dispatch_started", "Local adapter began processing; no network submission",
                    {"submission_id": t.id}, synthetic=True)
    a.attempts += 1; t.status = "AWAITING_EXTERNAL_RESULT"
    engine.set_state(a, r, "AWAITING_EXTERNAL_RESULT")
    engine.evidence(db, user, p, a, "test_package_received", "Synthetic adapter received immutable package; result not yet verified",
                    {"package_hash": t.package_hash}, synthetic=True)
    return finish(db, user, p, "test_package_dispatched")


@router.post("/submission/verify")
def verify_result(project_id: str, data: Version, user: User = Depends(current_user),
                  db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id); t = latest_submission(db, p); package_current(db, p, t)
    if t.status.startswith("SIMULATED_"):
        return engine.view(db, user, p)
    a, r = engine.checked_node(db, p, "submit", data.expected_version, {"AWAITING_EXTERNAL_RESULT"})
    if t.status != "AWAITING_EXTERNAL_RESULT":
        raise HTTPException(409, "No test-adapter result is available")
    t.status = "SIMULATED_" + t.outcome
    t.result_json = canonical({"simulation": True, "adapter": "LOCAL_TEST_V1", "reference": "TEST-" + t.id,
                              "status": t.status, "package_hash": t.package_hash,
                              "notice": "Synthetic result only. Not submitted to, accepted by, or verified with a government or professional."})
    engine.set_state(a, r, {"ACCEPTED": "COMPLETED_VERIFIED", "REJECTED": "FAILED",
                           "CORRECTION_REQUIRED": "CORRECTION_REQUIRED"}[t.outcome])
    engine.evidence(db, user, p, a, "synthetic_result", t.status + " — verified local TEST result only",
                    json.loads(t.result_json), synthetic=True)
    return finish(db, user, p, "test_result_verified")


@router.post("/actions/{key}/cancel")
def cancel(project_id: str, key: str, data: Accept, user: User = Depends(current_user),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    a, r = engine.checked_node(db, p, key, data.expected_version, set(engine.STATES) - {"COMPLETED_VERIFIED", "CANCELLED"})
    engine.set_state(a, r, "CANCELLED")
    if key == "submit":
        t = db.scalar(select(TestSubmission).where(TestSubmission.project_id == p.id)
                      .order_by(TestSubmission.created_at.desc()))
        if t and t.status in ("AUTHORIZED", "AWAITING_EXTERNAL_RESULT"):
            t.status = "CANCELLED"
    engine.evidence(db, user, p, a, "cancelled", "Customer cancelled this orchestration action; existing documents retained")
    return finish(db, user, p, "orchestrator_action_cancelled")


@router.post("/regulatory/collect")
def collect(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db),
            _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    if not engine.rows(db, p):
        raise HTTPException(409, "Start the orchestrator first")
    items, errors = collect_sources()
    added = 0
    for item in items:
        facts = item["facts"]; content_hash = signing.sha(canonical(facts).encode())
        exists = db.scalar(select(RegulatorySourceRevision).where(
            RegulatorySourceRevision.project_id == p.id, RegulatorySourceRevision.source_key == item["key"],
            RegulatorySourceRevision.content_hash == content_hash))
        if exists:
            continue
        previous = db.scalar(select(RegulatorySourceRevision).where(
            RegulatorySourceRevision.project_id == p.id, RegulatorySourceRevision.source_key == item["key"])
                             .order_by(RegulatorySourceRevision.checked_at.desc()))
        s = RegulatorySourceRevision(project_id=p.id, source_key=item["key"], source_url=item["url"],
                                      facts_json=canonical(facts), content_hash=content_hash)
        db.add(s); db.flush()
        c = RegulatoryChangeRecord(project_id=p.id, source_revision_id=s.id,
            previous_revision_id=previous.id if previous else None,
            change_type="SOURCE_CONTENT_CHANGED" if previous else "FIRST_SOURCE_OBSERVATION",
            legal_status=facts["legal_status"], effective_date=facts.get("effective_date"))
        db.add(c); db.flush()
        a, r = engine.create_action(db, user, p, "regulatory:" + c.id, "Review official source: " + facts["title"],
                                    "Regulatory intelligence / Mission Control", [])
        engine.set_state(a, r, "AWAITING_CUSTOMER_APPROVAL")
        db.add(ExecutionTask(tenant_id=user.tenant_id, business_id=p.business_id, horizon="today",
            task="Review possible regulatory relevance: " + facts["title"], budget="0", kpi="regulatory:" + c.id))
        engine.evidence(db, user, p, a, "official_source_observed", "Official source collected; legal applicability NOT verified",
                        {"source_hash": content_hash, "change_type": c.change_type})
        added += 1
    result = finish(db, user, p, "official_sources_collected")
    result["collection"] = {"status": "VERIFIED_PUBLIC_SOURCES_COLLECTED" if items else "UNAVAILABLE_NOT_VERIFIED",
                            "added": added, "errors": errors}
    return result


@router.post("/regulatory/{change_id}/review")
def review(project_id: str, change_id: str, data: Review, user: User = Depends(current_user),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    p = writable(db, user, project_id)
    c = db.scalar(select(RegulatoryChangeRecord).where(RegulatoryChangeRecord.project_id == p.id,
                                                     RegulatoryChangeRecord.id == change_id))
    if not c:
        raise HTTPException(404, "Source change not found")
    source = db.get(RegulatorySourceRevision, c.source_revision_id)
    if signing.sha(canonical(json.loads(source.facts_json)).encode()) != source.content_hash:
        raise HTTPException(409, "Official-source record integrity check failed")
    result = db.execute(update(RegulatoryChangeRecord).where(
        RegulatoryChangeRecord.id == c.id, RegulatoryChangeRecord.version == data.expected_version,
        RegulatoryChangeRecord.review_status == "PENDING_HUMAN_REVIEW")
        .values(review_status=data.decision, version=data.expected_version + 1))
    if result.rowcount != 1:
        raise HTTPException(409, "Review changed. Reload before continuing")
    a, r = engine.rows(db, p)["regulatory:" + c.id]
    status = "INFORMATION_REQUIRED" if data.decision == "NEEDS_PROFESSIONAL_REVIEW" else "COMPLETED_VERIFIED"
    engine.set_state(a, r, status)
    task = db.scalar(select(ExecutionTask).where(ExecutionTask.tenant_id == user.tenant_id,
        ExecutionTask.business_id == p.business_id, ExecutionTask.kpi == "regulatory:" + c.id))
    if task:
        task.status = "done" if status == "COMPLETED_VERIFIED" else "todo"
    engine.evidence(db, user, p, a, "human_source_review", "Customer review: " + data.decision +
                    "; not legal advice, a rule update, or a completion certificate")
    return finish(db, user, p, "regulatory_review_recorded")
