"""Add project dependency metadata, TEST evidence and source-backed review history."""
from alembic import op
import sqlalchemy as sa

revision = "g0008"
down_revision = "g0007"
branch_labels = None
depends_on = None


def upgrade():
    def col(name, typ=sa.String(), fk=None, nullable=False, **kw):
        return sa.Column(name, typ, *([sa.ForeignKey(fk)] if fk else []), nullable=nullable, **kw)
    def table(name, columns, constraints=()):
        op.create_table(name, col("id", primary_key=True), col("project_id", fk="business_projects.id"),
                        *columns, *constraints)
        op.create_index(f"ix_{name}_project_id", name, ["project_id"])
    table("project_actions", [
        col("action_id", fk="execution_action_records.id", unique=True),
        col("action_key", sa.String(100)), col("subsystem", sa.String(80)),
        col("dependencies_json", sa.Text()), col("requirements_json", sa.Text()),
        col("version", sa.Integer()), col("attempts", sa.Integer()),
        col("deadline", sa.DateTime(timezone=True), nullable=True),
        col("completed_at", sa.DateTime(timezone=True), nullable=True),
    ], [sa.UniqueConstraint("project_id", "action_key", name="uq_project_action_key")])
    table("test_document_signatures", [
        col("document_id", fk="generated_documents.id"), col("user_id", fk="users.id"),
        col("request_key", sa.String(80)), col("envelope_json", sa.Text()),
        col("artifact_hash", sa.String(64)), col("audit_mac", sa.String(64)),
        col("revoked_at", sa.DateTime(timezone=True), nullable=True), col("created_at", sa.DateTime(timezone=True)),
    ], [sa.UniqueConstraint("project_id", "request_key", name="uq_test_signature_request")])
    table("test_submissions", [
        col("signature_id", fk="test_document_signatures.id"), col("request_key", sa.String(80)),
        col("outcome", sa.String(40)), col("status", sa.String(40)), col("package_hash", sa.String(64)),
        col("result_json", sa.Text()), col("created_at", sa.DateTime(timezone=True)),
    ], [sa.UniqueConstraint("project_id", "request_key", name="uq_test_submission_request")])
    table("regulatory_source_revisions", [
        col("source_key", sa.String(120)), col("source_url", sa.Text()), col("content_hash", sa.String(64)),
        col("facts_json", sa.Text()), col("checked_at", sa.DateTime(timezone=True)),
    ], [sa.UniqueConstraint("project_id", "source_key", "content_hash", name="uq_project_source_hash")])
    table("regulatory_change_records", [
        col("source_revision_id", fk="regulatory_source_revisions.id", unique=True),
        col("previous_revision_id", fk="regulatory_source_revisions.id", nullable=True),
        col("change_type", sa.String(40)), col("legal_status", sa.String(30)),
        col("effective_date", sa.String(10), nullable=True), col("review_status", sa.String(40)),
        col("version", sa.Integer()), col("created_at", sa.DateTime(timezone=True)),
    ])


def downgrade():
    tables = ("regulatory_change_records", "regulatory_source_revisions", "test_submissions",
              "test_document_signatures", "project_actions")
    if any(op.get_bind().scalar(sa.text(f"SELECT COUNT(*) FROM {t}")) for t in tables):
        raise RuntimeError("Refusing to remove populated orchestration or signature/source evidence")
    for name in tables:
        op.drop_table(name)
