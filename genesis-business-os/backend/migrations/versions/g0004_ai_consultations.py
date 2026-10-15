"""Add consented offline consultations; preserve all earlier migration identifiers."""
from alembic import op
import sqlalchemy as sa

revision = "g0004"
down_revision = "g0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_consultations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("journey_id", sa.String(), sa.ForeignKey("onboarding_journeys.id"), nullable=False),
        sa.Column("turns_json", sa.Text(), nullable=False),
        sa.Column("journey_version", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("detail_mode", sa.String(12), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("journey_id", name="uq_consultation_journey"),
    )
    for column in ("tenant_id", "user_id", "journey_id"):
        op.create_index(f"ix_ai_consultations_{column}", "ai_consultations", [column])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT COUNT(*) FROM ai_consultations")):
        raise RuntimeError("Refusing to delete saved consultations; explicit data-preservation review required")
    op.drop_table("ai_consultations")
