import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc)

class Tenant(Base):
    __tablename__='tenants'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str]=mapped_column(String(120))
    lockdown: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class User(Base):
    __tablename__='users'; __table_args__=(UniqueConstraint('email'),)
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(ForeignKey('tenants.id'), index=True)
    email: Mapped[str]=mapped_column(String(254), index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[str]=mapped_column(String(30), default='owner')
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class FounderProfile(Base):
    __tablename__='founder_profiles'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    owner_id: Mapped[str|None]=mapped_column(String, index=True, nullable=True)
    user_id: Mapped[str|None]=mapped_column(String, index=True, nullable=True)
    version: Mapped[int]=mapped_column(Integer, default=1)
    objective: Mapped[str|None]=mapped_column(Text, nullable=True)
    constraints_json: Mapped[str]=mapped_column(Text, default='{}')
    profile_json: Mapped[str]=mapped_column(Text, default='{}')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Business(Base):
    __tablename__='businesses'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    name: Mapped[str]=mapped_column(String(160))
    lifecycle_state: Mapped[str]=mapped_column(String(40), default='simulated')
    twin_json: Mapped[str]=mapped_column(Text, default='{}')
    twin_version: Mapped[int]=mapped_column(Integer, default=1)
    proof_state_json: Mapped[str]=mapped_column(Text, default='{}')
    route_context_json: Mapped[str]=mapped_column(Text, default='{}')
    next_turn_json: Mapped[str]=mapped_column(Text, default='{}')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class OnboardingJourney(Base):
    __tablename__ = 'onboarding_journeys'
    __table_args__ = (UniqueConstraint('tenant_id', 'user_id', 'stage', name='uq_journey_user_stage'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    business_id: Mapped[str] = mapped_column(ForeignKey('businesses.id'), index=True)
    stage: Mapped[str] = mapped_column(String(8))
    answers_json: Mapped[str] = mapped_column(Text, default='{}')
    language: Mapped[str] = mapped_column(String(5), default='en')
    detail_mode: Mapped[str] = mapped_column(String(12), default='simple')
    version: Mapped[int] = mapped_column(Integer, default=1)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AIConsultation(Base):
    __tablename__ = "ai_consultations"
    __table_args__ = (UniqueConstraint("journey_id", name="uq_consultation_journey"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("onboarding_journeys.id"), index=True)
    turns_json: Mapped[str] = mapped_column(Text, default="[]")
    journey_version: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    language: Mapped[str] = mapped_column(String(5))
    detail_mode: Mapped[str] = mapped_column(String(12))
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ConsultationPrivacy(Base):
    __tablename__ = "consultation_privacy"
    journey_id: Mapped[str] = mapped_column(ForeignKey("onboarding_journeys.id"), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BusinessIdea(Base):
    __tablename__ = "business_ideas"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    facts_json: Mapped[str] = mapped_column(Text)
    plans_json: Mapped[str] = mapped_column(Text, default="[]")
    selected_plan: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IdeaRevision(Base):
    __tablename__ = "idea_revisions"
    __table_args__ = (UniqueConstraint("idea_id", "version", name="uq_idea_revision"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    idea_id: Mapped[str] = mapped_column(ForeignKey("business_ideas.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    facts_json: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BusinessProject(Base):
    __tablename__ = "business_projects"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    idea_id: Mapped[str] = mapped_column(ForeignKey("business_ideas.id"), unique=True)
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    plan_json: Mapped[str] = mapped_column(Text)
    budget_cents: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(20), default="PLANNING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BusinessPassport(Base):
    """Minimal customer-authorized project profile, not verified identity."""
    __tablename__ = "business_passports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), unique=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    fields_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DocumentWorkflow(Base):
    __tablename__ = "document_workflows"
    __table_args__ = (UniqueConstraint("project_id", "template_key", name="uq_project_document_template"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    template_key: Mapped[str] = mapped_column(String(80))
    template_version: Mapped[int] = mapped_column(Integer, default=1)
    fields_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class GeneratedDocument(Base):
    """Immutable structured document source; file bytes are rendered on demand."""
    __tablename__ = "generated_documents"
    __table_args__ = (UniqueConstraint("workflow_id", "revision", name="uq_document_revision"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("document_workflows.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    template_version: Mapped[int] = mapped_column(Integer, default=1)
    source_json: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DocumentApproval(Base):
    __tablename__ = "document_approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey("generated_documents.id"), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(60), default="SIGNATURE_PREPARATION_ONLY")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PartnerApplication(Base):
    __tablename__ = "partner_applications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    details_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="APPLICATION")
    version: Mapped[int] = mapped_column(Integer, default=1)
    review_json: Mapped[str] = mapped_column(Text, default="{}")
    review_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PartnerPromotion(Base):
    __tablename__ = "partner_promotions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    partner_id: Mapped[str] = mapped_column(ForeignKey("partner_applications.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    partner_permission_reference: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    attribution_code: Mapped[str] = mapped_column(String, default=uid, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Evidence(Base):
    __tablename__='evidence'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    business_id: Mapped[str]=mapped_column(String, index=True)
    classification: Mapped[str]=mapped_column(String(40))
    value: Mapped[str]=mapped_column(Text)
    source_ref: Mapped[str]=mapped_column(Text, default='user')
    confidence: Mapped[int]=mapped_column(Integer, default=50)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class Decision(Base):
    __tablename__='decisions'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    business_id: Mapped[str]=mapped_column(String, index=True)
    question: Mapped[str]=mapped_column(Text)
    risk_tier: Mapped[int]=mapped_column(Integer, default=1)
    status: Mapped[str]=mapped_column(String(30), default='draft')
    recommendation_json: Mapped[str]=mapped_column(Text, default='{}')
    approved_by: Mapped[str|None]=mapped_column(String, nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class GrowthCampaign(Base):
    __tablename__ = 'growth_campaigns'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'), index=True)
    creator_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(160))
    objective: Mapped[str] = mapped_column(String(1200))
    audience: Mapped[str] = mapped_column(String(500))
    channel: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text, default='')
    planned_budget_cents: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default='DRAFT')
    version: Mapped[int] = mapped_column(Integer, default=1)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__='audit_events'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    actor_id: Mapped[str]=mapped_column(String, index=True)
    action: Mapped[str]=mapped_column(String(120))
    resource_type: Mapped[str]=mapped_column(String(80))
    resource_id: Mapped[str]=mapped_column(String(80))
    details_json: Mapped[str]=mapped_column(Text, default='{}')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class ActualObservation(Base):
    __tablename__='actual_observations'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    business_id: Mapped[str]=mapped_column(String, index=True)
    key: Mapped[str]=mapped_column(String(120), index=True)
    value: Mapped[str]=mapped_column(String(120))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
class DecisionLedger(Base):
    __tablename__='decision_ledger'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    business_id: Mapped[str]=mapped_column(String, index=True)
    decision_id: Mapped[str]=mapped_column(String, index=True)
    payload_hash: Mapped[str]=mapped_column(String(64))
    payload_json: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class SessionRecord(Base):
    __tablename__='sessions'
    id: Mapped[str]=mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    user_id: Mapped[str]=mapped_column(String, index=True)
    csrf_hash: Mapped[str]=mapped_column(String(64))
    ip_hash: Mapped[str]=mapped_column(String(64))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    last_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)

class ExecutionTask(Base):
    __tablename__='execution_tasks'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str]=mapped_column(String, index=True)
    business_id: Mapped[str]=mapped_column(String, index=True)
    horizon: Mapped[str]=mapped_column(String(32))
    task: Mapped[str]=mapped_column(Text)
    budget: Mapped[str]=mapped_column(String(64), default='0')
    status: Mapped[str]=mapped_column(String(32), default='todo')
    kpi: Mapped[str]=mapped_column(String(200), default='')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now)

class CommunityPost(Base):
    __tablename__='community_posts'
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    tenant_id: Mapped[str]=mapped_column(String,index=True)
    user_id: Mapped[str]=mapped_column(String,index=True)
    display_name: Mapped[str]=mapped_column(String,default='Founder')
    category: Mapped[str]=mapped_column(String,default='ASK')
    body: Mapped[str]=mapped_column(Text)
    moderation_status: Mapped[str]=mapped_column(String(24),default='visible',index=True)
    deleted: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class CommunityReply(Base):
    __tablename__='community_replies'
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    post_id: Mapped[str]=mapped_column(String,index=True)
    tenant_id: Mapped[str]=mapped_column(String,index=True)
    user_id: Mapped[str]=mapped_column(String,index=True)
    display_name: Mapped[str]=mapped_column(String,default='Founder')
    body: Mapped[str]=mapped_column(Text)
    moderation_status: Mapped[str]=mapped_column(String(24),default='visible',index=True)
    deleted: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class CommunityReport(Base):
    __tablename__='community_reports'
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    reporter_user_id: Mapped[str]=mapped_column(String,index=True)
    target_type: Mapped[str]=mapped_column(String(20))
    target_id: Mapped[str]=mapped_column(String,index=True)
    reason: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(24),default='open',index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class CommunityBlock(Base):
    __tablename__='community_blocks'
    __table_args__=(UniqueConstraint('blocker_user_id','blocked_user_id'),)
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    blocker_user_id: Mapped[str]=mapped_column(String,index=True)
    blocked_user_id: Mapped[str]=mapped_column(String,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class ExecutionActionRecord(Base):
    __tablename__='execution_action_records'
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    tenant_id: Mapped[str]=mapped_column(String,index=True)
    business_id: Mapped[str]=mapped_column(String,index=True)
    user_id: Mapped[str]=mapped_column(String,index=True)
    point_key: Mapped[str]=mapped_column(String(80),index=True)
    mode: Mapped[str]=mapped_column(String(16))
    risk_tier: Mapped[int]=mapped_column(Integer)
    status: Mapped[str]=mapped_column(String(32),default='PROPOSED',index=True)
    payload_json: Mapped[str]=mapped_column(Text,default='{}')
    result_json: Mapped[str]=mapped_column(Text,default='{}')
    idempotency_key: Mapped[str]=mapped_column(String(80),unique=True,index=True)
    approved_by: Mapped[str|None]=mapped_column(String,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    dispatch_started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    provider_reference: Mapped[str|None]=mapped_column(Text,nullable=True)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)

class ExecutionReceiptRecord(Base):
    __tablename__='execution_receipt_records'
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    tenant_id: Mapped[str]=mapped_column(String,index=True)
    business_id: Mapped[str]=mapped_column(String,index=True)
    action_id: Mapped[str]=mapped_column(String,index=True)
    evidence_type: Mapped[str]=mapped_column(String(80),index=True)
    summary: Mapped[str]=mapped_column(Text)
    external_reference: Mapped[str|None]=mapped_column(Text,nullable=True)
    metadata_json: Mapped[str]=mapped_column(Text,default='{}')
    provenance: Mapped[str]=mapped_column(String(24),default='USER',index=True)
    trusted: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class ProviderWebhookEvent(Base):
    __tablename__='provider_webhook_events'
    __table_args__=(UniqueConstraint('provider','event_id'),)
    id: Mapped[str]=mapped_column(String,primary_key=True,default=uid)
    tenant_id: Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    provider: Mapped[str]=mapped_column(String(32),index=True)
    event_id: Mapped[str]=mapped_column(String(160),index=True)
    event_type: Mapped[str]=mapped_column(String(120),index=True)
    verified_signature: Mapped[bool]=mapped_column(Boolean,default=False)
    payload_hash: Mapped[str]=mapped_column(String(64))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)


class ProjectAction(Base):
    """Project dependency metadata around the existing shared execution record."""
    __tablename__ = "project_actions"
    __table_args__ = (UniqueConstraint("project_id", "action_key", name="uq_project_action_key"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), index=True)
    action_id: Mapped[str] = mapped_column(ForeignKey("execution_action_records.id"), unique=True)
    action_key: Mapped[str] = mapped_column(String(100))
    subsystem: Mapped[str] = mapped_column(String(80))
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]")
    requirements_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TestDocumentSignature(Base):
    __tablename__ = "test_document_signatures"
    __table_args__ = (UniqueConstraint("project_id", "request_key", name="uq_test_signature_request"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("generated_documents.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    request_key: Mapped[str] = mapped_column(String(80))
    envelope_json: Mapped[str] = mapped_column(Text)
    artifact_hash: Mapped[str] = mapped_column(String(64))
    audit_mac: Mapped[str] = mapped_column(String(64))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TestSubmission(Base):
    __tablename__ = "test_submissions"
    __table_args__ = (UniqueConstraint("project_id", "request_key", name="uq_test_submission_request"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), index=True)
    signature_id: Mapped[str] = mapped_column(ForeignKey("test_document_signatures.id"))
    request_key: Mapped[str] = mapped_column(String(80))
    outcome: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="AUTHORIZED")
    package_hash: Mapped[str] = mapped_column(String(64))
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RegulatorySourceRevision(Base):
    __tablename__ = "regulatory_source_revisions"
    __table_args__ = (UniqueConstraint("project_id", "source_key", "content_hash", name="uq_project_source_hash"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), index=True)
    source_key: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    facts_json: Mapped[str] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RegulatoryChangeRecord(Base):
    __tablename__ = "regulatory_change_records"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("business_projects.id"), index=True)
    source_revision_id: Mapped[str] = mapped_column(ForeignKey("regulatory_source_revisions.id"), unique=True)
    previous_revision_id: Mapped[str | None] = mapped_column(ForeignKey("regulatory_source_revisions.id"), nullable=True)
    change_type: Mapped[str] = mapped_column(String(40))
    legal_status: Mapped[str] = mapped_column(String(30), default="UNVERIFIED")
    effective_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    review_status: Mapped[str] = mapped_column(String(40), default="PENDING_HUMAN_REVIEW")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
