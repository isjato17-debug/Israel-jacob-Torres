"""Phase 1: automatic internal work, genuine saved evidence, scoped approval pauses."""
import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from sqlalchemy import select, func

from app.db import SessionLocal
from app.models import (DocumentWorkflow, GeneratedDocument, DocumentApproval, ExecutionReceiptRecord,
                        ProjectAction, User, SessionRecord, Tenant, BusinessProject, AuditEvent)
from test_autoform import PASS, DETAILS
from test_big_consultation import account
from test_idea_vault import action
from test_unified_intelligence import env, chosen


def create(env):
    c, h, _, _, _ = env
    idea = chosen(env)
    response = action(c, h, idea, "develop")
    assert response.status_code == 200, response.text
    project = response.json()
    return project, f"/api/v2/projects/{project['id']}/orchestrator", f"/api/v2/projects/{project['id']}/execution"


def node(view, key):
    return next(a for a in view["actions"] if a["key"] == key)


def test_independent_tasks_execute_while_agreement_paused_and_get_is_read_only(env):
    c, h, _, _, _ = env
    project, root, docs = create(env)
    view = c.get(root).json()
    assert node(view, "native:context")["status"] == "COMPLETED_VERIFIED"
    assert node(view, "native:requirements")["status"] == "COMPLETED_VERIFIED"
    assert node(view, "native:sources")["status"] == "FAILED"
    assert node(view, "prepare")["status"] == "INFORMATION_REQUIRED"
    assert node(view, "approve")["status"] == "NOT_READY"
    assert view["signatures"] == view["submissions"] == []
    assert view["autonomous"]["mode"] == "NO_PAID_AI_INTERNAL_TOOLS_ONLY"
    for output in view["autonomous"]["outputs"]:
        assert output["integrity_verified"] and len(output["content_hash"]) == 64
    matrix = next(o["output"] for o in view["autonomous"]["outputs"] if o["key"] == "native:requirements")
    for requirement in matrix["requirements"]:
        assert requirement["jurisdiction"] == "NY" and requirement["official_source"].startswith("https://")
        assert requirement["effective_date"] is None and requirement["verification_status"] == "UNVERIFIED"
    workflow = c.get(docs).json()["workflow"]
    assert workflow["status"] == "DRAFT" and workflow["missing"] and not workflow["documents"]
    # Real market validation and financing are not invented by the internal executor.
    assert all(t["status"] == "todo" for t in view["planning_tasks"])
    with SessionLocal() as db:
        counts = [db.scalar(select(func.count()).select_from(m)) for m in (ProjectAction, ExecutionReceiptRecord, AuditEvent)]
    for _ in range(3):
        assert c.get(root).status_code == 200
    with SessionLocal() as db:
        assert counts == [db.scalar(select(func.count()).select_from(m)) for m in (ProjectAction, ExecutionReceiptRecord, AuditEvent)]
    for _ in range(2):
        assert c.post(root + "/run", headers=h, json={}).status_code == 200
    resumed = c.get(root).json()
    assert node(resumed, "native:sources")["attempts"] == 1
    assert len(resumed["autonomous"]["outputs"]) == len(view["autonomous"]["outputs"])
    assert c.get(f"/api/v2/projects/{project['id']}").json()["budget_cents"] == 300000


def fill(c, h, docs):
    response = c.put(docs + "/passport", headers=h,
                     json={"expected_version": 0, "consent": True, "fields": PASS})
    assert response.status_code == 200, response.text
    workflow = response.json()["workflow"]
    assert all(workflow["fields"][k] == v for k, v in PASS.items())
    response = c.patch(docs + "/document", headers=h,
                       json={"expected_version": workflow["version"], "fields": {**workflow["fields"], **DETAILS}})
    assert response.status_code == 200, response.text
    return response.json()["workflow"]


def test_fields_save_automatically_generates_verifies_and_pauses_for_exact_approval(env):
    c, h, user, _, _ = env
    project, root, docs = create(env)
    workflow = fill(c, h, docs)
    assert workflow["status"] == "GENERATED" and len(workflow["documents"]) == 1
    document = workflow["latest_document"]
    download = c.get(docs + f"/documents/{document['id']}/download")
    assert hashlib.sha256(download.content).hexdigest() == document["content_hash"]
    view = c.get(root).json()
    assert node(view, "prepare")["status"] == "COMPLETED_VERIFIED"
    assert node(view, "approve")["status"] == "AWAITING_CUSTOMER_APPROVAL"
    assert node(view, "sign")["status"] == "NOT_READY"
    output = next(o for o in view["autonomous"]["outputs"] if o["key"] == "prepare")
    assert output["integrity_verified"] and output["output"]["document_id"] == document["id"]
    assert output["output"]["status"] == "PREPARED_UNSIGNED_NOT_SENT"
    assert c.post("/api/auth/logout", headers=h).status_code == 200
    assert c.get(root).status_code == 401
    login = c.post("/api/auth/login", json={"email": user["email"], "password": "BIG-foundation-safe-2026!"})
    assert login.status_code == 200
    h = {"X-CSRF-Token": login.json()["csrf"]}
    assert c.post(root + "/run", headers=h, json={}).status_code == 200
    assert c.get(docs).json()["workflow"]["latest_document"]["id"] == document["id"]
    approval = {"expected_version": workflow["version"], "document_id": document["id"],
                "content_hash": document["content_hash"], "confirmed": True}
    response = c.post(docs + "/approve", headers=h, json=approval)
    assert response.status_code == 200, response.text
    resumed = c.get(root).json()
    assert node(resumed, "approve")["status"] == "COMPLETED_VERIFIED"
    assert node(resumed, "sign")["status"] == "AWAITING_CUSTOMER_APPROVAL"
    assert resumed["signatures"] == [] and resumed["submissions"] == []
    # Corrections create a new immutable revision; old approval never transfers.
    approved = response.json()["workflow"]
    correction = c.patch(docs + "/document", headers=h, json={
        "expected_version": approved["version"], "fields": {**approved["fields"], "price_cents": 24000}})
    assert correction.status_code == 200
    latest = correction.json()["workflow"]["latest_document"]
    assert latest["id"] != document["id"] and latest["revision"] == 2 and latest["approval"] is None
    assert c.get(docs + f"/documents/{document['id']}/download").content == download.content
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(DocumentApproval).where(
            DocumentApproval.document_id == document["id"])) == 1


def test_failures_are_isolated_and_retries_bounded(env):
    c, h, _, _, _ = env
    with patch("app.services.project_execution.requirement_matrix", side_effect=RuntimeError("private detail")):
        _, root, docs = create(env)
        view = c.get(root).json()
        assert node(view, "native:requirements")["status"] == "FAILED"
        assert node(view, "native:context")["status"] == "COMPLETED_VERIFIED"
        assert c.get(docs).json()["workflow"]["missing"]
        assert "private detail" not in json.dumps(view)
        for _ in range(5):
            assert c.post(root + "/run", headers=h, json={"retry_failed": True}).status_code == 200
        assert node(c.get(root).json(), "native:requirements")["attempts"] == 3


def test_exact_test_authorization_advances_local_adapter_never_external(env):
    c, h, _, _, _ = env
    _, root, docs = create(env)
    workflow = fill(c, h, docs)
    document = workflow["latest_document"]
    assert c.post(docs + "/approve", headers=h, json={
        "expected_version": workflow["version"], "document_id": document["id"],
        "content_hash": document["content_hash"], "confirmed": True}).status_code == 200
    view = c.get(root).json()
    response = c.post(root + "/sign", headers=h, json={
        "expected_version": node(view, "sign")["version"], "document_id": document["id"],
        "content_hash": document["content_hash"], "typed_name": PASS["representative_name"],
        "password": "BIG-foundation-safe-2026!", "request_key": str(uuid.uuid4()),
        "reviewed": True, "consent": True, "disclosure_version": "test-sign-v1"})
    assert response.status_code == 200, response.text
    view = response.json()
    assert view["submissions"] == []
    response = c.post(root + "/submission/authorize", headers=h, json={
        "expected_version": node(view, "submit")["version"], "signature_id": view["signatures"][0]["id"],
        "request_key": str(uuid.uuid4()), "outcome": "ACCEPTED", "confirmed": True})
    assert response.status_code == 200, response.text
    final = response.json()
    assert node(final, "submit")["status"] == "COMPLETED_VERIFIED"
    assert final["submissions"][0]["status"] == "SIMULATED_ACCEPTED"
    assert final["submissions"][0]["simulation"] is True
    assert final["submissions"][0]["result"]["notice"].startswith("Synthetic result only")
    count = len(node(final, "submit")["evidence"])
    assert c.post(root + "/run", headers=h, json={}).status_code == 200
    assert len(node(c.get(root).json(), "submit")["evidence"]) == count
    signature_id = final["signatures"][0]["id"]
    assert c.post(root + f"/signatures/{signature_id}/withdraw", headers=h,
                  json={"confirmed": True}).status_code == 200
    assert c.post(root + "/run", headers=h, json={}).status_code == 200
    assert node(c.get(root).json(), "sign")["status"] == "AWAITING_CUSTOMER_APPROVAL"


def test_run_is_scoped_csrf_locked_and_cannot_authorize_external_work(env):
    c, h, user, _, _ = env
    _, root, _ = create(env)
    assert c.post(root + "/run", json={}).status_code == 403
    for extra in ({"paid_ai": True}, {"external_actions": True}, {"retry_failed": "yes"}):
        assert c.post(root + "/run", headers=h, json=extra).status_code == 422
    other, oh, ou = account()
    for same_tenant in (False, True):
        if same_tenant:
            with SessionLocal() as db:
                db.get(User, ou["id"]).tenant_id = user["tenant_id"]
                for session in db.scalars(select(SessionRecord).where(SessionRecord.user_id == ou["id"])):
                    session.tenant_id = user["tenant_id"]
                db.commit()
        assert other.post(root + "/run", headers=oh, json={}).status_code == 404
    other.close()
    with SessionLocal() as db:
        db.get(Tenant, user["tenant_id"]).lockdown = True
        db.commit()
    assert c.post(root + "/run", headers=h, json={}).status_code == 423


def test_concurrent_resume_is_idempotent_and_no_op_does_not_change_action_versions(env):
    c, h, _, _, _ = env
    project, root, docs = create(env)
    before = c.get(root).json()
    with ThreadPoolExecutor(max_workers=3) as pool:
        responses = list(pool.map(lambda _: c.post(root + "/run", headers=h, json={}), range(3)))
    assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
    after = c.get(root).json()
    assert [(a["key"], a["version"]) for a in before["actions"]] == [
        (a["key"], a["version"]) for a in after["actions"]]
    assert before["autonomous"]["outputs"] == after["autonomous"]["outputs"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(DocumentWorkflow).where(
            DocumentWorkflow.project_id == project["id"])) == 1
        assert db.scalar(select(func.count()).select_from(ProjectAction).where(
            ProjectAction.project_id == project["id"])) == 13


def test_uncommitted_execution_rolls_back_then_resumes_cleanly(env):
    c, h, user, _, _ = env
    project, root, docs = create(env)
    before = c.get(root).json()
    # Force an eligible internal task, simulate a process ending before commit.
    with SessionLocal() as db:
        from app.models import ExecutionActionRecord
        from app.services.project_execution import advance
        from app.services.business_orchestrator import rows, set_state
        p = db.get(BusinessProject, project["id"])
        u = db.get(User, user["id"])
        a, record = rows(db, p)["native:requirements"]
        set_state(a, record, "NOT_READY")
        advance(db, u, p)
        db.rollback()
    after = c.get(root).json()
    assert before["autonomous"]["outputs"] == after["autonomous"]["outputs"]
    assert node(before, "native:requirements")["version"] == node(after, "native:requirements")["version"]
    assert c.post(root + "/run", headers=h, json={}).status_code == 200
    assert node(c.get(root).json(), "native:requirements")["status"] == "COMPLETED_VERIFIED"


def test_tampered_output_is_never_presented_as_verified_and_retry_preserves_history(env):
    c, h, _, _, _ = env
    _, root, _ = create(env)
    view = c.get(root).json()
    action_id = next(a["id"] for a in view["actions"] if a["key"] == "native:requirements")
    with SessionLocal() as db:
        project_action = db.get(ProjectAction, action_id)
        receipt = db.scalar(select(ExecutionReceiptRecord).where(
            ExecutionReceiptRecord.action_id == project_action.action_id,
            ExecutionReceiptRecord.evidence_type == "internal_output"))
        original_id = receipt.id
        data = json.loads(receipt.metadata_json)
        data["output"]["classification"] = "TAMPERED"
        receipt.metadata_json = json.dumps(data)
        db.commit()
    bad = c.get(root).json()
    assert node(bad, "native:requirements")["status"] == "FAILED"
    output = next(o for o in bad["autonomous"]["outputs"] if o["key"] == "native:requirements")
    assert output["integrity_verified"] is False
    response = c.post(root + "/run", headers=h, json={"retry_failed": True})
    assert response.status_code == 200, response.text
    output = next(o for o in response.json()["autonomous"]["outputs"] if o["key"] == "native:requirements")
    assert output["integrity_verified"] is True
    assert node(response.json(), "native:requirements")["status"] == "COMPLETED_VERIFIED"
    with SessionLocal() as db:
        assert "TAMPERED" in db.get(ExecutionReceiptRecord, original_id).metadata_json


def test_all_five_existing_prepare_tools_execute_without_external_dispatch(env):
    from app.services.execution_hub import prepare
    from app.services.execution_preparation import PREPARATIONS
    c, h, _, _, _ = env
    with patch("app.services.execution_preparation.prepare", wraps=prepare) as prepared, \
            patch("app.services.execution_hub.execute", side_effect=AssertionError("External dispatch prohibited")) as external:
        _, root, _ = create(env)
        assert prepared.call_count == 5 and not external.called
        view = c.get(root).json()
        for key in PREPARATIONS:
            assert node(view, "tool:" + key)["status"] == "COMPLETED_VERIFIED"
            output = next(o for o in view["autonomous"]["outputs"] if o["key"] == "tool:" + key)
            assert output["integrity_verified"]
            assert output["output"]["scope"] == "INTERNAL_DRAFT_NOT_SENT_OR_PUBLISHED"
            assert output["output"]["artifact"]["content"]
            assert output["output"]["classification"] == "DETERMINISTIC_DRAFT_FROM_UNVERIFIED_SELECTED_PLAN"
        assert c.post(root + "/run", headers=h, json={}).status_code == 200
        assert prepared.call_count == 5 and not external.called
