"""Bounded internal execution using existing project actions, AutoForm and receipt stores.

No model calls, background loops, spending, signatures or government submissions.
Every advancement is a customer-scoped transaction; interrupted work rolls back.
"""
import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError

from ..models import BusinessProject, ExecutionReceiptRecord
from . import business_orchestrator as engine, document_engine as forms
from .test_signing import sha
from .execution_preparation import PREPARATIONS
from .execution_hub import CATALOG

CAPABILITIES = {
    "native:context": ("Prepare financial, Digital Twin, Board and Founder DNA analysis", ["strategy"]),
    "native:requirements": ("Prepare jurisdiction and official-source requirements matrix", []),
    "native:sources": ("Collect bounded official public-source observations", []),
    **{"tool:" + key: (CATALOG[key].title, ["strategy"]) for key in PREPARATIONS},
}
RESTRICTIONS = [
    "No paid AI: this executor uses existing deterministic tools, not live AI.",
    "No spending, billing, real signature, government submission or deployment.",
    "Prepared analysis is not verified demand, funding, legal applicability or business launch.",
    "TEST signature and submission actions require separate scoped customer consent.",
]
MAX_ATTEMPTS = 3


def latest_output(db, record):
    receipt = db.scalar(select(ExecutionReceiptRecord).where(
        ExecutionReceiptRecord.action_id == record.id,
        ExecutionReceiptRecord.evidence_type == "internal_output")
        .order_by(ExecutionReceiptRecord.created_at.desc(), ExecutionReceiptRecord.id.desc()))
    if not receipt:
        return None
    item = json.loads(receipt.metadata_json)
    item["integrity_verified"] = sha(forms.canonical(item["output"]).encode()) == item["content_hash"]
    return item


def save_output(db, user, p, action, record, output, *, status="COMPLETED_VERIFIED"):
    content_hash = sha(forms.canonical(output).encode())
    old = latest_output(db, record)
    if not old or not old["integrity_verified"] or old["content_hash"] != content_hash:
        engine.evidence(db, user, p, action, "internal_output", "Stored internal preparation; not external execution",
                        {"output": output, "content_hash": content_hash})
    record.result_json = forms.canonical({"content_hash": content_hash, "scope": "INTERNAL_PREPARATION"})
    engine.set_state(action, record, status)
    db.flush()
    verified = latest_output(db, record)
    if not verified or not verified["integrity_verified"]:
        raise ValueError("Stored output integrity verification failed")


def requirement_matrix(p):
    plan = json.loads(p.plan_json)
    jurisdiction = plan.get("business_strategy", {}).get("jurisdiction")
    # Legacy projects carry the jurisdiction in their idea instead; supplied by caller.
    return {"classification": "REFERENCE_MATRIX_NOT_LEGAL_VERIFICATION",
            "requirements": [{**r, "jurisdiction": jurisdiction, "official_source": r["official_url"],
                              "effective_date": None, "verification_status": "UNVERIFIED",
                              "source_content_checked_at": None,
                              "notice": "Official reference only; applicability and effective date need review."}
                             for r in plan["requirements"]],
            "professional_help": plan["service_needs"]}


def prepare_agreement(db, user, p, action, record):
    from ..v2 import documents
    if not documents.context(db, user, p)["supported"]:
        engine.set_state(action, record, "BLOCKED")
        record.result_json = forms.canonical({"reason": "No existing AutoForm template supports this business."})
        return
    workflow = documents.ensure_workflow(db, user, p)
    fields = forms.AgreementFields(**json.loads(workflow.fields_json)).model_dump()
    saved = documents.passport(db, p)
    if saved and workflow.status == "DRAFT":
        reused = {**fields, **{k: v for k, v in json.loads(saved.fields_json).items() if v and not fields.get(k)}}
        if reused != fields:
            documents.change(db, workflow, workflow.version, fields_json=forms.canonical(reused))
            fields = reused
            documents.audit(db, user, "passport_reused_for_internal_preparation", workflow.id,
                            workflow.version, passport_version=saved.version)
    missing = forms.missing(fields)
    if missing:
        engine.set_state(action, record, "INFORMATION_REQUIRED")
        record.result_json = forms.canonical({"missing": missing})
        return
    if workflow.status == "DRAFT":
        documents.generate_document(db, user, p, workflow, workflow.version)
        db.flush()
    _, document = engine.document_state(db, p)
    if not document or forms.digest(json.loads(document.source_json)) != document.content_hash:
        raise ValueError("Generated document integrity verification failed")
    save_output(db, user, p, action, record,
                {"document_id": document.id, "revision": document.revision,
                 "content_hash": document.content_hash, "workflow_id": workflow.id,
                 "status": "PREPARED_UNSIGNED_NOT_SENT", "scope": "INTERNAL_PREPARATION"})


def execute(db, user, p, key, action, record):
    if key.startswith("tool:"):
        from .execution_preparation import prepare_for_project
        save_output(db, user, p, action, record, prepare_for_project(db, p, key.removeprefix("tool:")))
    elif key == "native:context":
        from ..v2.documents import context
        value = context(db, user, p)["assistant"]
        save_output(db, user, p, action, record,
                    {"project_id": p.id, "budget_cents": p.budget_cents,
                     "selected_plan": json.loads(p.plan_json), **value})
    elif key == "native:requirements":
        from ..models import BusinessIdea
        value = requirement_matrix(p)
        jurisdiction = json.loads(db.get(BusinessIdea, p.idea_id).facts_json)["jurisdiction"]
        for requirement in value["requirements"]:
            requirement["jurisdiction"] = jurisdiction
        save_output(db, user, p, action, record, value)
    elif key == "native:sources":
        from .regulatory_collection import collect_sources, store_sources
        items, errors = collect_sources()
        store_sources(db, user, p, items)
        save_output(db, user, p, action, record,
                    {"sources": items, "errors": errors, "observed_at": datetime.now(timezone.utc).isoformat(),
                     "legal_verification": "UNVERIFIED", "effective_date": None,
                     "scope": "PUBLIC_READ_ONLY_NO_CUSTOMER_DATA_SENT"},
                    status="FAILED" if errors or not items else "COMPLETED_VERIFIED")
    elif key == "prepare":
        prepare_agreement(db, user, p, action, record)


def advance(db, user, p, *, enable=False, retry_failed=False):
    """One finite pass. Each operation is idempotent and independent failures are isolated.

    A no-op project UPDATE serializes runners in SQLite and PostgreSQL. No remote
    writes are in this transaction. Retries require explicit input and are bounded.
    """
    try:
        db.flush()
        db.execute(update(BusinessProject).where(
            BusinessProject.id == p.id, BusinessProject.tenant_id == user.tenant_id,
            BusinessProject.user_id == user.id).values(stage=BusinessProject.stage))
    except OperationalError:
        db.rollback()
        raise HTTPException(409, "Execution is busy. Reload and retry; no operation was replayed.") from None
    nodes = engine.rows(db, p)
    if not nodes or (not enable and "native:context" not in nodes):
        return
    for key, (title, deps) in CAPABILITIES.items():
        if key not in nodes:
            action, record = engine.create_action(db, user, p, key, title, "Existing internal tools", deps)
            req = json.loads(action.requirements_json)
            req["customer_authorization"] = False
            req["authorization_basis"] = "Customer requested project preparation; no external write authorized"
            action.requirements_json = forms.canonical(req)
            nodes[key] = action, record
    engine.reconcile(db, user, p)
    # Only an exact package explicitly authorized through the existing TEST
    # approval path can advance. This adapter is local; it never sends a request.
    action, record = nodes["submit"]
    if record.status in ("AUTHORIZED", "AWAITING_EXTERNAL_RESULT"):
        from ..v2.orchestrator import dispatch_package, verify_package
        db.flush()
        if record.status == "AUTHORIZED":
            dispatch_package(db, user, p, action.version)
            db.flush()
        verify_package(db, user, p, action.version)
    # Sources run last so public-read failures cannot prevent local preparation.
    for key in ("native:requirements", "native:context", *("tool:" + k for k in PREPARATIONS),
                "prepare", "native:sources"):
        action, record = nodes[key]
        if record.status in ("CANCELLED", "BLOCKED"):
            continue
        if record.status == "COMPLETED_VERIFIED":
            previous = latest_output(db, record)
            if previous and not previous["integrity_verified"]:
                engine.set_state(action, record, "FAILED")
                record.result_json = forms.canonical({"reason": "Stored result integrity failed; review and retry required."})
                db.flush()
                if not retry_failed:
                    continue
            # AutoForm invalidates prepare when edited, so approved revisions are never regenerated.
            if key != "prepare" and record.status == "COMPLETED_VERIFIED":
                continue
            _, document = engine.document_state(db, p)
            if previous and document and previous["output"].get("document_id") == document.id:
                continue
        if record.status == "FAILED" and (not retry_failed or action.attempts >= MAX_ATTEMPTS):
            continue
        if any(nodes[dep][1].status != "COMPLETED_VERIFIED" for dep in json.loads(action.dependencies_json)):
            continue
        # A draft with the same missing inputs is a pause, not a failed retry.
        if key == "prepare" and action.attempts >= MAX_ATTEMPTS and record.status == "FAILED":
            continue
        try:
            with db.begin_nested():
                if key != "prepare":
                    engine.set_state(action, record, "IN_PROGRESS")
                execute(db, user, p, key, action, record)
                if record.status != "INFORMATION_REQUIRED":
                    action.attempts += 1
                db.flush()
        except Exception:
            # Do not persist provider text, customer input or exception strings in logs.
            engine.set_state(action, record, "FAILED")
            action.attempts += 1
            record.result_json = forms.canonical({"reason": "Operation failed safely; independent work continued.",
                                                 "retry_limit": MAX_ATTEMPTS})
            engine.evidence(db, user, p, action, "internal_failure",
                            "Internal operation failed; no external completion is claimed")
            db.flush()
    from .funding import refresh
    refresh(db, user, p)
    engine.reconcile(db, user, p)


def execution_view(db, user, p, nodes):
    enabled = "native:context" in nodes
    outputs, requests = [], []
    for key, (action, record) in nodes.items():
        output = latest_output(db, record)
        title = json.loads(action.requirements_json)["title"]
        status = record.status
        if output:
            outputs.append({"key": key, "title": title, **output})
            if not output["integrity_verified"]:
                status = "FAILED"
        if status in ("INFORMATION_REQUIRED", "AWAITING_CUSTOMER_APPROVAL", "BLOCKED", "FAILED"):
            result = json.loads(record.result_json)
            reason = result.get("reason")
            if output and not output["integrity_verified"]:
                reason = "Stored result integrity failed; review and retry required."
            if status == "FAILED":
                reason = ("Retry limit reached; correct inputs or request operator support."
                          if action.attempts >= MAX_ATTEMPTS else
                          reason or "Official source reads were unavailable or incomplete. Local preparation continued.")
            if not reason:
                reason = ("Review this exact revision and explicitly approve; B.I.G. cannot act as you."
                          if status == "AWAITING_CUSTOMER_APPROVAL" else
                          "Provide the missing information once; eligible preparation resumes automatically.")
            requests.append({"key": key,
                "kind": "approval" if status == "AWAITING_CUSTOMER_APPROVAL" else
                        "failure" if status == "FAILED" else
                        "blocked" if status == "BLOCKED" else "information",
                "title": title, "fields": [{"key": k, "label": forms.LABELS[k]} for k in result.get("missing", [])],
                "reason": reason,
            })
    return {"enabled": enabled, "mode": "NO_PAID_AI_INTERNAL_TOOLS_ONLY", "outputs": outputs,
            "requests": requests, "restrictions": RESTRICTIONS}
