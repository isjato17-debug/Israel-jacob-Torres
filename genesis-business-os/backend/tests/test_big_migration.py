"""Preservation proof on disposable SQLite; optional explicitly local disposable PostgreSQL."""
import json
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text, select, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models import (Tenant, User, Business, OnboardingJourney, GrowthCampaign, AIConsultation,
                        PartnerApplication, PartnerPromotion, BusinessIdea, IdeaRevision,
                        BusinessProject, ConsultationPrivacy, BusinessPassport, DocumentWorkflow,
                        GeneratedDocument, DocumentApproval)
from app.services.document_engine import AgreementFields, canonical, digest

ROOT = Path(__file__).resolve().parents[1]


def verify_upgrade(url):
    environment = {**os.environ, "GENESIS_ENV": "development", "GENESIS_DATABASE_URL": url}
    def alembic(*args):
        result = subprocess.run(
            ["python", "-m", "alembic", *args], cwd=ROOT, env=environment,
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout + result.stderr
    alembic("upgrade", "g0003")
    engine = create_engine(url)
    with Session(engine) as db:
        tenant = Tenant(name="Disposable preservation fixture")
        db.add(tenant); db.flush()
        user = User(tenant_id=tenant.id, email="preserve@example.com", password_hash="not-a-login")
        business = Business(tenant_id=tenant.id, name="Preserved baseline business")
        db.add_all([user, business]); db.flush()
        journey = OnboardingJourney(
            tenant_id=tenant.id, user_id=user.id, business_id=business.id,
            stage="start", answers_json=json.dumps({"state": "NY"}), language="es",
        )
        campaign = GrowthCampaign(
            tenant_id=tenant.id, creator_id=user.id, title="Preserved campaign",
            objective="Preserve review and planned cents", audience="Existing fixture",
            channel="website", content="Original planning text", planned_budget_cents=1234,
        )
        db.add_all([journey, campaign]); db.commit()
    preserved = ("tenants", "users", "businesses", "onboarding_journeys", "growth_campaigns")
    def snapshot():
        with engine.connect() as conn:
            return {name: [tuple(row) for row in conn.execute(text(f"SELECT * FROM {name} ORDER BY id"))]
                    for name in preserved}
    before = snapshot()
    alembic("upgrade", "g0004")
    assert snapshot() == before
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "g0004"
        assert conn.scalar(text("SELECT COUNT(*) FROM ai_consultations")) == 0
    with Session(engine) as db:
        saved = db.scalar(select(OnboardingJourney))
        db.add(AIConsultation(
            tenant_id=saved.tenant_id, user_id=saved.user_id, journey_id=saved.id,
            journey_version=saved.version, language="es", detail_mode="simple",
            turns_json='[]',
        ))
        db.commit()
    alembic("upgrade", "g0005")
    with Session(engine) as db:
        saved = db.scalar(select(OnboardingJourney))
        partner = PartnerApplication(
            tenant_id=saved.tenant_id, applicant_id=saved.user_id, details_json='{"preserve":true}',
        )
        db.add(partner); db.flush()
        db.add(PartnerPromotion(
            tenant_id=saved.tenant_id, partner_id=partner.id,
            title="Preserve private promotion", content="Preserved internal content",
        ))
        db.commit()
    alembic("upgrade", "g0006")
    with Session(engine) as db:
        saved = db.scalar(select(OnboardingJourney))
        idea = BusinessIdea(tenant_id=saved.tenant_id, user_id=saved.user_id,
                            facts_json='{"concept":"Preserve private cleaning idea","budget_cents":300000}')
        db.add(idea); db.flush()
        db.add(IdeaRevision(idea_id=idea.id, version=1, facts_json=idea.facts_json, action="created"))
        db.add(BusinessProject(tenant_id=saved.tenant_id, user_id=saved.user_id, idea_id=idea.id,
                              business_id=saved.business_id, name="Preserved private project",
                              budget_cents=300000, plan_json='{"key":"start_smart","name":"Preserved plan"}'))
        db.add(ConsultationPrivacy(tenant_id=saved.tenant_id, user_id=saved.user_id,
                                   journey_id=saved.id, status="REVOKED", version=2))
        db.commit()
    alembic("upgrade", "g0007")
    with Session(engine) as db:
        project = db.scalar(select(BusinessProject))
        fields = AgreementFields(business_name="Preserved cleaning", representative_name="Provider",
                                 client_name="Client", price_cents=10000).model_dump()
        db.add(BusinessPassport(project_id=project.id, tenant_id=project.tenant_id,
                               user_id=project.user_id, fields_json=canonical(fields)))
        workflow = DocumentWorkflow(project_id=project.id, tenant_id=project.tenant_id,
            user_id=project.user_id, template_key="cleaning_service_agreement",
            fields_json=canonical(fields), status="READY_FOR_SIGNATURE")
        db.add(workflow); db.flush()
        source = {"fields": fields, "template_version": 1, "prepared_at": "2026-10-15",
                  "project_name": project.name, "plan_name": "Preserved plan", "jurisdiction": "NY"}
        old_document_hash = digest(source)
        doc = GeneratedDocument(workflow_id=workflow.id, revision=1, source_json=canonical(source),
                                content_hash=old_document_hash)
        db.add(doc); db.flush()
        db.add(DocumentApproval(document_id=doc.id, user_id=project.user_id, content_hash=old_document_hash))
        db.commit()
    def all_original_rows():
        with engine.connect() as conn:
            return {name: [tuple(row) for row in conn.execute(text(f'SELECT * FROM "{name}" ORDER BY 1'))]
                    for name in inspect(engine).get_table_names()
                    if name != "alembic_version" and name not in (
                        "project_actions", "test_document_signatures", "test_submissions",
                        "regulatory_source_revisions", "regulatory_change_records")}
    before_m0 = all_original_rows()
    alembic("upgrade", "head")
    assert all_original_rows() == before_m0
    assert snapshot() == before
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == "g0008"
        assert conn.scalar(text("SELECT COUNT(*) FROM ai_consultations")) == 1
        assert conn.scalar(text("SELECT COUNT(*) FROM partner_applications")) == 1
        assert conn.scalar(text("SELECT COUNT(*) FROM partner_promotions")) == 1
        for name in ("business_ideas", "idea_revisions", "business_projects", "consultation_privacy"):
            assert conn.scalar(text(f"SELECT COUNT(*) FROM {name}")) == 1
        for name in ("business_passports", "document_workflows", "generated_documents", "document_approvals"):
            assert conn.scalar(text(f"SELECT COUNT(*) FROM {name}")) == 1
        for name in ("project_actions", "test_document_signatures", "test_submissions",
                     "regulatory_source_revisions", "regulatory_change_records"):
            assert conn.scalar(text(f"SELECT COUNT(*) FROM {name}")) == 0
    with Session(engine) as db:
        assert digest(json.loads(db.scalar(select(GeneratedDocument)).source_json)) == old_document_hash
    assert "No new upgrade operations detected" in alembic("check")
    engine.dispose()


def test_additive_upgrade_preserves_data(tmp_path):
    verify_upgrade(f"sqlite:///{tmp_path / 'migration.sqlite'}")


@pytest.mark.skipif(not os.getenv("GENESIS_DISPOSABLE_MIGRATION_TEST_URL"), reason="Optional disposable PostgreSQL not selected")
def test_postgres_additive_upgrade_preserves_data():
    url = os.environ["GENESIS_DISPOSABLE_MIGRATION_TEST_URL"]
    parsed = make_url(url)
    assert parsed.host == "127.0.0.1" and parsed.database.startswith("big_phase2_test")
    verify_upgrade(url)
