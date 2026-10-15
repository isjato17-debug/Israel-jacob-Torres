"""Persistent project coordination reusing shared action/receipt and Mission Control records."""
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from ..models import (ProjectAction, ExecutionActionRecord, ExecutionReceiptRecord, BusinessIdea,
                      DocumentWorkflow, GeneratedDocument, TestDocumentSignature, TestSubmission,
                      RegulatoryChangeRecord, RegulatorySourceRevision, ExecutionTask)
from .document_engine import canonical, digest
from .idea_planning import prepare_plans
from .test_signing import verify, sha, DISCLOSURE, DISCLOSURE_VERSION
from .business_registry import registry, government_workflows

STATES = ("NOT_READY", "INFORMATION_REQUIRED", "READY", "AWAITING_CUSTOMER_APPROVAL", "AUTHORIZED",
          "IN_PROGRESS", "AWAITING_EXTERNAL_RESULT", "COMPLETED_VERIFIED", "CORRECTION_REQUIRED", "FAILED", "CANCELLED")
SPECS = {
    "strategy": ("Review selected strategy and alternatives", "Executive Board / Three-Plan Engine", []),
    "prepare": ("Prepare current agreement", "AutoForm / Business Passport", ["strategy"]),
    "approve": ("Approve exact current document", "AutoForm", ["prepare"]),
    "sign": ("Create TEST signature evidence", "Test signing", ["approve"]),
    "submit": ("DirectSubmit TEST package and receipt", "DirectSubmit test adapter", ["sign"]),
}


def rows(db, p):
    return {a.action_key: (a, db.get(ExecutionActionRecord, a.action_id))
            for a in db.scalars(select(ProjectAction).where(ProjectAction.project_id == p.id))}


def create_action(db, user, p, key, title, subsystem, deps):
    r = ExecutionActionRecord(tenant_id=user.tenant_id, user_id=user.id, business_id=p.business_id,
        point_key="orchestrator." + key, mode="SIMULATE" if key in ("sign", "submit") else "PREPARE",
        risk_tier=1, status="NOT_READY", payload_json="{}", idempotency_key="project:" + p.id + ":" + key)
    db.add(r); db.flush()
    a = ProjectAction(project_id=p.id, action_id=r.id, action_key=key, subsystem=subsystem,
                      dependencies_json=canonical(deps), requirements_json=canonical({
                          "title": title, "information": ["Current project and exact document"] if key in ("approve", "sign", "submit") else [],
                          "customer_authorization": key not in ("prepare",),
                          "provider": "LOCAL_TEST_ONLY" if key in ("sign", "submit") else "NONE",
                          "scope": "TEST_ONLY" if key in ("sign", "submit") else "INTERNAL_PREPARATION"}))
    db.add(a); db.flush()
    return a, r


def set_state(a, r, status):
    if status != r.status:
        r.status = status; a.version += 1
        a.completed_at = datetime.now(timezone.utc) if status == "COMPLETED_VERIFIED" else None


def evidence(db, user, p, a, kind, summary, metadata=None, synthetic=False):
    db.add(ExecutionReceiptRecord(tenant_id=user.tenant_id, business_id=p.business_id, action_id=a.action_id,
        evidence_type=kind, summary=summary, metadata_json=canonical(metadata or {}),
        provenance="TEST_ONLY" if synthetic else "SYSTEM", trusted=True))


def document_state(db, p):
    w = db.scalar(select(DocumentWorkflow).where(DocumentWorkflow.project_id == p.id))
    d = db.scalar(select(GeneratedDocument).where(GeneratedDocument.workflow_id == w.id)
                  .order_by(GeneratedDocument.revision.desc())) if w else None
    return w, d


def current_signature(db, p, d):
    if not d:
        return None
    candidates = db.scalars(select(TestDocumentSignature).where(
        TestDocumentSignature.project_id == p.id, TestDocumentSignature.document_id == d.id,
        TestDocumentSignature.revoked_at.is_(None)).order_by(TestDocumentSignature.created_at.desc()))
    return next((s for s in candidates if verify(s, d)), None)


def reconcile(db, user, p):
    """Called inside existing document transactions, never by a read-only GET."""
    nodes = rows(db, p)
    if not nodes:
        return
    w, d = document_state(db, p)
    signed = current_signature(db, p, d) if w and w.status == "READY_FOR_SIGNATURE" else None
    for key in SPECS:
        a, r = nodes[key]
        if r.status == "CANCELLED":
            continue
        deps = json.loads(a.dependencies_json)
        satisfied = all(nodes[x][1].status == "COMPLETED_VERIFIED" for x in deps)
        if not satisfied:
            set_state(a, r, "CORRECTION_REQUIRED" if r.status in (
                "COMPLETED_VERIFIED", "AUTHORIZED", "AWAITING_EXTERNAL_RESULT") else "NOT_READY")
        elif key == "strategy":
            if r.status != "COMPLETED_VERIFIED":
                set_state(a, r, "AWAITING_CUSTOMER_APPROVAL")
        elif key == "prepare":
            set_state(a, r, "COMPLETED_VERIFIED" if d and w.status != "DRAFT" else "INFORMATION_REQUIRED")
        elif key == "approve":
            set_state(a, r, "COMPLETED_VERIFIED" if w.status == "READY_FOR_SIGNATURE" else "AWAITING_CUSTOMER_APPROVAL")
        elif key == "sign":
            set_state(a, r, "COMPLETED_VERIFIED" if signed else "AWAITING_CUSTOMER_APPROVAL")
        elif key == "submit":
            if not signed:
                set_state(a, r, "NOT_READY")
            elif r.status == "NOT_READY":
                set_state(a, r, "AWAITING_CUSTOMER_APPROVAL")
            latest = db.scalar(select(TestSubmission).where(TestSubmission.project_id == p.id)
                               .order_by(TestSubmission.created_at.desc()))
            if latest and latest.signature_id != signed.id:
                set_state(a, r, "AWAITING_CUSTOMER_APPROVAL")


def checked_node(db, p, key, version, allowed):
    node = rows(db, p).get(key)
    if not node:
        raise HTTPException(409, "Start the orchestrator first")
    a, r = node
    if r.status not in allowed:
        raise HTTPException(409, "Action prerequisites or authorization are not satisfied")
    result = db.execute(update(ProjectAction).where(ProjectAction.id == a.id, ProjectAction.version == version)
                        .values(version=version + 1).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Action changed. Reload before continuing; nothing was replayed")
    db.refresh(a)
    return a, r


def strategy(db, p):
    facts = json.loads(db.get(BusinessIdea, p.idea_id).facts_json)
    plans = prepare_plans(facts)
    selected = json.loads(p.plan_json)
    preferred = next(x for x in plans if x["recommended"])
    return {"selected": selected["key"], "recommended": preferred["key"],
            "reason": preferred["recommendation_reason"],
            "classification": "DETERMINISTIC_FROM_UNVERIFIED_INPUTS_NOT_LIVE_AI",
            "comparisons": [{"key": x["key"], "name": x["name"], "funding_gap_cents": x["funding_gap_cents"],
                "advantages": [f"Estimated reserve and economics follow the {x['name']} scenario",
                               "Within stated capital" if not x["funding_gap_cents"] else "Separate funding decision required"],
                "disadvantages": [f"Funding gap ${x['funding_gap_cents']/100:,.2f}", "Unverified demand and capacity"],
                "assumptions": x["assumptions"], "risks": x["risks"]} for x in plans],
            "evidence_gaps": ["No verified market research, competition, supplier quotes, legal structure or financing terms",
                              "Goals are preserved but not interpreted by live AI; no profitability guarantee",
                              "License, liability, work authorization and actual staffing need separate review"],
            "mitigation": ["Validate demand before spending", "Replace estimates with quotes and test downside cash flow",
                           "Retain the selected plan only after reviewing its gap and alternatives"]}


def view(db, user, p):
    nodes = rows(db, p)
    actions = []
    for key, (a, r) in nodes.items():
        receipts = db.scalars(select(ExecutionReceiptRecord).where(ExecutionReceiptRecord.action_id == r.id)).all()
        deps = json.loads(a.dependencies_json)
        req = json.loads(a.requirements_json)
        actions.append({"id": a.id, "key": key, "title": req["title"], "subsystem": a.subsystem,
            "status": r.status, "version": a.version, "dependencies": deps, "requirements": req,
            "blocked_by": [x for x in deps if nodes[x][1].status != "COMPLETED_VERIFIED"],
            "attempts": a.attempts, "deadline": a.deadline, "completed_at": a.completed_at,
            "evidence": [{"type": x.evidence_type, "summary": x.summary, "provenance": x.provenance} for x in receipts]})
    signatures = []
    for s in db.scalars(select(TestDocumentSignature).where(TestDocumentSignature.project_id == p.id)
                       .order_by(TestDocumentSignature.created_at.desc())):
        d = db.get(GeneratedDocument, s.document_id); envelope = json.loads(s.envelope_json)
        signatures.append({"id": s.id, "document_id": d.id, "document_hash": envelope["document_hash"],
            "artifact_hash": s.artifact_hash, "typed_name": envelope["typed_name"], "created_at": s.created_at,
            "revoked": s.revoked_at is not None, "integrity_verified": verify(s, d)})
    submissions = [{"id": t.id, "signature_id": t.signature_id, "status": t.status, "outcome": t.outcome,
                    "package_hash": t.package_hash, "result": json.loads(t.result_json), "simulation": True}
                   for t in db.scalars(select(TestSubmission).where(TestSubmission.project_id == p.id)
                                       .order_by(TestSubmission.created_at.desc()))]
    changes = []
    for c in db.scalars(select(RegulatoryChangeRecord).where(RegulatoryChangeRecord.project_id == p.id)):
        source = db.get(RegulatorySourceRevision, c.source_revision_id); facts = json.loads(source.facts_json)
        if sha(canonical(facts).encode()) != source.content_hash:
            raise HTTPException(409, "Official-source record integrity check failed")
        changes.append({"id": c.id, "version": c.version, "title": facts["title"], "source_url": source.source_url,
            "content_hash": source.content_hash, "checked_at": source.checked_at, "change_type": c.change_type,
            "legal_status": c.legal_status, "effective_date": c.effective_date, "review_status": c.review_status,
            "previous_revision_id": c.previous_revision_id, "facts": facts})
    return {"initialized": bool(nodes), "scope": "INTERNAL_PREPARATION_AND_EXPLICIT_TESTS_ONLY", "actions": actions,
            "next_actions": [a["title"] for a in actions if not a["blocked_by"] and a["status"] in
                             ("READY", "INFORMATION_REQUIRED", "AWAITING_CUSTOMER_APPROVAL", "AUTHORIZED", "AWAITING_EXTERNAL_RESULT")],
            "strategy": strategy(db, p), "signing": {"disclosure": DISCLOSURE, "disclosure_version": DISCLOSURE_VERSION,
                "method": "TYPED_NAME_PASSWORD_REAUTH_TEST_ONLY", "passkeys": "NOT_IMPLEMENTED_NO_BIOMETRICS_COLLECTED"},
            "signatures": signatures, "submissions": submissions, "changes": changes,
            "registry": registry(), "government_workflows": government_workflows()}
