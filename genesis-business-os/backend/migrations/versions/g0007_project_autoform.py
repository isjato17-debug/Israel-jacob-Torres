"""Add private project Passport and versioned document workflow; preserve prior rows."""
from alembic import op
import sqlalchemy as sa

revision = "g0007"
down_revision = "g0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("business_passports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("business_projects.id"), nullable=False, unique=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("fields_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("document_workflows",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("business_projects.id"), nullable=False),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("template_key", sa.String(80), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("fields_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "template_key", name="uq_project_document_template"),
    )
    op.create_table("generated_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_id", sa.String(), sa.ForeignKey("document_workflows.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("source_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workflow_id", "revision", name="uq_document_revision"),
    )
    op.create_table("document_approvals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("generated_documents.id"), nullable=False, unique=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table, columns in {
        "business_passports": ("tenant_id", "user_id"),
        "document_workflows": ("project_id", "tenant_id", "user_id"),
        "generated_documents": ("workflow_id",),
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade():
    db = op.get_bind()
    tables = ("document_approvals", "generated_documents", "document_workflows", "business_passports")
    if any(db.scalar(sa.text(f"SELECT COUNT(*) FROM {t}")) for t in tables):
        raise RuntimeError("Refusing to remove saved document sources, approvals or Passport data")
    for t in tables:
        op.drop_table(t)
