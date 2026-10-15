"""Customer-private ideas and projects. Reuses Business, financials and Mission Control tasks."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import BusinessIdea, IdeaRevision, BusinessProject, Business, ExecutionTask, AuditEvent, User
from ..security import current_user, ensure_not_lockdown, require_csrf
from ..services.idea_planning import prepare_plans
from ..services.product_engine import execution_plan
from .catalog import STATES
from .journey import utc

router = APIRouter(prefix="/api/v2", tags=["Private ideas and projects"])


class IdeaFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concept: str = Field(min_length=5, max_length=1200)
    industry: str = Field(default="", max_length=120)
    jurisdiction: str
    budget_cents: int = Field(ge=0, le=100_000_000, strict=True)
    goals: str = Field(default="", max_length=1200)
    preferences: str = Field(default="", max_length=1200)
    notes: str = Field(default="", max_length=3000)
    assumptions: str = Field(default="", max_length=2000)

    @field_validator("concept", "industry", "goals", "preferences", "notes", "assumptions", mode="before")
    @classmethod
    def strip(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("jurisdiction")
    @classmethod
    def state(cls, value):
        if value not in dict(STATES) and value != "DC":
            raise ValueError("Select a U.S. state or DC")
        return value


class CreateIdea(IdeaFacts):
    consent: Literal[True]


class Version(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1, strict=True)


class EditIdea(IdeaFacts):
    expected_version: int = Field(ge=1, strict=True)


class Selection(Version):
    plan_key: Literal["start_smart", "build_strong", "grow_big"]


def owned_idea(db, user, idea_id):
    item = db.scalar(select(BusinessIdea).where(
        BusinessIdea.id == idea_id, BusinessIdea.tenant_id == user.tenant_id,
        BusinessIdea.user_id == user.id,
    ))
    if not item:
        raise HTTPException(404, "Idea not found")
    return item


def project_for_idea(db, item):
    return db.scalar(select(BusinessProject).where(BusinessProject.idea_id == item.id))


def describe(db, item):
    project = project_for_idea(db, item)
    history = db.scalars(select(IdeaRevision).where(
        IdeaRevision.idea_id == item.id).order_by(IdeaRevision.version)).all()
    return {
        **json.loads(item.facts_json), "id": item.id, "version": item.version,
        "status": item.status, "selected_plan": item.selected_plan,
        "plans": json.loads(item.plans_json), "project_id": project.id if project else None,
        "created_at": utc(item.created_at), "updated_at": utc(item.updated_at),
        "history": [{"version": r.version, "action": r.action, "created_at": utc(r.created_at)} for r in history],
    }


def record(db, user, item, action):
    db.add(IdeaRevision(idea_id=item.id, version=item.version, facts_json=item.facts_json, action=action))
    db.add(AuditEvent(
        tenant_id=user.tenant_id, actor_id=user.id, action=f"idea_{action}",
        resource_type="business_idea", resource_id=item.id,
        details_json=json.dumps({"version": item.version, "status": item.status}),
    ))


def change(db, user, item, expected, values, action):
    ensure_not_lockdown(db, user)
    if item.version != expected:
        raise HTTPException(409, "Idea changed. Reload and review before retrying.")
    result = db.execute(update(BusinessIdea).where(
        BusinessIdea.id == item.id, BusinessIdea.user_id == user.id,
        BusinessIdea.tenant_id == user.tenant_id, BusinessIdea.version == expected,
    ).values(**values, version=expected + 1, updated_at=datetime.now(timezone.utc))
      .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Idea changed. Reload and review before retrying.")
    db.refresh(item)
    record(db, user, item, action)


def editable(item):
    if item.status in ("ARCHIVED", "DEVELOPED"):
        raise HTTPException(409, "Restore an archived idea first. Developed project assumptions cannot be rewritten.")


def finish(db, item):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Idea changed in another session. Reload before retrying.") from None
    db.refresh(item)
    return describe(db, item)


@router.get("/ideas")
def list_ideas(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(BusinessIdea).where(
        BusinessIdea.tenant_id == user.tenant_id, BusinessIdea.user_id == user.id,
    ).order_by(BusinessIdea.updated_at.desc())).all()
    return {"ideas": [describe(db, r) for r in rows]}


@router.post("/ideas")
def create(payload: CreateIdea, user: User = Depends(current_user),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    item = BusinessIdea(tenant_id=user.tenant_id, user_id=user.id,
                        facts_json=json.dumps(payload.model_dump(exclude={"consent"})))
    db.add(item); db.flush()
    record(db, user, item, "created")
    return finish(db, item)


@router.get("/ideas/{idea_id}")
def get(idea_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return describe(db, owned_idea(db, user, idea_id))


@router.patch("/ideas/{idea_id}")
def edit(idea_id: str, payload: EditIdea, user: User = Depends(current_user),
         db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned_idea(db, user, idea_id)
    editable(item)
    change(db, user, item, payload.expected_version, {
        "facts_json": json.dumps(payload.model_dump(exclude={"expected_version"})),
        "plans_json": "[]", "selected_plan": None, "status": "DRAFT",
    }, "edited")
    return finish(db, item)


@router.post("/ideas/{idea_id}/archive")
def archive(idea_id: str, payload: Version, user: User = Depends(current_user),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned_idea(db, user, idea_id)
    if item.status == "ARCHIVED":
        raise HTTPException(409, "Idea is already archived")
    change(db, user, item, payload.expected_version, {"status": "ARCHIVED"}, "archived")
    return finish(db, item)


@router.post("/ideas/{idea_id}/restore")
def restore(idea_id: str, payload: Version, user: User = Depends(current_user),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned_idea(db, user, idea_id)
    if item.status != "ARCHIVED":
        raise HTTPException(409, "Idea is not archived")
    status = "DEVELOPED" if project_for_idea(db, item) else "PLANNED" if json.loads(item.plans_json) else "DRAFT"
    change(db, user, item, payload.expected_version, {"status": status}, "restored")
    return finish(db, item)


@router.post("/ideas/{idea_id}/generate")
def generate(idea_id: str, payload: Version, user: User = Depends(current_user),
             db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned_idea(db, user, idea_id)
    editable(item)
    plans = prepare_plans(json.loads(item.facts_json))
    change(db, user, item, payload.expected_version, {
        "plans_json": json.dumps(plans), "selected_plan": None, "status": "PLANNED",
    }, "plans_prepared")
    return finish(db, item)


@router.post("/ideas/{idea_id}/select")
def choose(idea_id: str, payload: Selection, user: User = Depends(current_user),
           db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    item = owned_idea(db, user, idea_id)
    editable(item)
    if payload.plan_key not in {p["key"] for p in json.loads(item.plans_json)}:
        raise HTTPException(409, "Prepare plans before selecting one")
    change(db, user, item, payload.expected_version, {"selected_plan": payload.plan_key}, "plan_selected")
    return finish(db, item)


def describe_project(db, project):
    tasks = db.scalars(select(ExecutionTask).where(
        ExecutionTask.tenant_id == project.tenant_id,
        ExecutionTask.business_id == project.business_id,
    ).order_by(ExecutionTask.created_at, ExecutionTask.id)).all()
    return {
        "id": project.id, "business_id": project.business_id, "idea_id": project.idea_id,
        "name": project.name, "stage": project.stage, "budget_cents": project.budget_cents,
        "plan": json.loads(project.plan_json), "created_at": utc(project.created_at),
        "checklist": [{"id": t.id, "horizon": t.horizon, "task": t.task, "budget": float(t.budget),
                       "status": t.status, "kpi": t.kpi} for t in tasks],
    }


@router.post("/ideas/{idea_id}/develop")
def develop(idea_id: str, payload: Version, user: User = Depends(current_user),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    item = owned_idea(db, user, idea_id)
    if item.status == "ARCHIVED":
        raise HTTPException(409, "Restore the idea before developing it")
    existing = project_for_idea(db, item)
    if existing:
        return describe_project(db, existing)  # Safe retry: never creates duplicate project/tasks.
    chosen = next((p for p in json.loads(item.plans_json) if p["key"] == item.selected_plan), None)
    if not chosen:
        raise HTTPException(409, "Select a prepared plan before creating a project")
    facts = json.loads(item.facts_json)
    change(db, user, item, payload.expected_version, {"status": "DEVELOPED"}, "developed")
    twin = {
        "monthly_revenue": chosen["monthly_revenue_cents"] / 100,
        "monthly_fixed_cost": chosen["monthly_fixed_cents"] / 100,
        "gross_margin": chosen["gross_margin"],
        "cash": max(0, facts["budget_cents"] - chosen["startup_total_cents"]) / 100,
        "classification": "UNVERIFIED_PLANNING_ESTIMATES",
    }
    business = Business(tenant_id=user.tenant_id, name=facts["concept"][:160],
                        lifecycle_state="planning", twin_json=json.dumps(twin),
                        route_context_json=json.dumps({"source": "private_idea", "owner_id": user.id}))
    db.add(business); db.flush()
    project = BusinessProject(tenant_id=user.tenant_id, user_id=user.id, idea_id=item.id,
                              business_id=business.id, name=business.name,
                              plan_json=json.dumps(chosen), budget_cents=facts["budget_cents"])
    db.add(project)
    # No task budget authorizes spending. Existing Mission Control provides status persistence.
    for task in execution_plan(facts["concept"], 0):
        db.add(ExecutionTask(
            id=task["id"], tenant_id=user.tenant_id, business_id=business.id,
            horizon=task["horizon"], task=task["task"], budget="0",
            status=task["status"], kpi=task["kpi"],
        ))
    db.add(ExecutionTask(
        tenant_id=user.tenant_id, business_id=business.id, horizon="today",
        task="Review jurisdiction requirements, professional service needs and funding gap before committing money.",
        budget="0", status="todo", kpi="reviewed",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Project creation changed in another session. Reload before retrying.") from None
    return describe_project(db, project)


@router.get("/projects")
def projects(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(BusinessProject).where(
        BusinessProject.tenant_id == user.tenant_id, BusinessProject.user_id == user.id,
    ).order_by(BusinessProject.created_at.desc())).all()
    return {"projects": [describe_project(db, r) for r in rows]}


@router.get("/projects/{project_id}")
def project(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(BusinessProject).where(
        BusinessProject.id == project_id, BusinessProject.tenant_id == user.tenant_id,
        BusinessProject.user_id == user.id,
    ))
    if not item:
        raise HTTPException(404, "Project not found")
    return describe_project(db, item)
