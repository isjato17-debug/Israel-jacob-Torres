"""Private partner intake and internal promotion preparation, additive only."""
from alembic import op
import sqlalchemy as sa

revision = "g0005"
down_revision = "g0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "partner_applications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("applicant_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("review_json", sa.Text(), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("tenant_id", "applicant_id"):
        op.create_index(f"ix_partner_applications_{column}", "partner_applications", [column])
    op.create_table(
        "partner_promotions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("partner_id", sa.String(), sa.ForeignKey("partner_applications.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("partner_permission_reference", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("attribution_code", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("tenant_id", "partner_id"):
        op.create_index(f"ix_partner_promotions_{column}", "partner_promotions", [column])


def downgrade():
    db = op.get_bind()
    for table in ("partner_promotions", "partner_applications"):
        if db.scalar(sa.text(f"SELECT COUNT(*) FROM {table}")):
            raise RuntimeError("Refusing to delete partner records without explicit preservation review")
    op.drop_table("partner_promotions")
    op.drop_table("partner_applications")
