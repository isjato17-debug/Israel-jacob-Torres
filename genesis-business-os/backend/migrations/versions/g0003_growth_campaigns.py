"""Add private campaign planning; no changes to existing business records."""
from alembic import op
import sqlalchemy as sa

revision = "g0003"
down_revision = "g0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "growth_campaigns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("creator_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("objective", sa.String(1200), nullable=False),
        sa.Column("audience", sa.String(500), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("planned_budget_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ["tenant_id", "creator_id"]:
        op.create_index(f"ix_growth_campaigns_{column}", "growth_campaigns", [column])


def downgrade():
    # Populated campaign records must be backed up and deletion explicitly approved.
    op.drop_table("growth_campaigns")
