"""Add account-bound saved journeys without changing existing business tables."""
from alembic import op
import sqlalchemy as sa

revision = "g0002"
down_revision = "g0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "onboarding_journeys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("business_id", sa.String(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("stage", sa.String(8), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("detail_mode", sa.String(12), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "stage", name="uq_journey_user_stage"),
    )
    for column in ["tenant_id", "user_id", "business_id"]:
        op.create_index(f"ix_onboarding_journeys_{column}", "onboarding_journeys", [column])


def downgrade():
    # Removes only new journey progress. Requires an explicit data-loss approval
    # or a verified restore plan on any database that contains customer journeys.
    op.drop_table("onboarding_journeys")
