"""Add private idea/project storage and consultation privacy state; no existing row edits."""
from alembic import op
import sqlalchemy as sa

revision = "g0006"
down_revision = "g0005"
branch_labels = None
depends_on = None


def ownership():
    return [
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
    ]


def upgrade():
    op.create_table(
        "consultation_privacy",
        sa.Column("journey_id", sa.String(), sa.ForeignKey("onboarding_journeys.id"), primary_key=True),
        *ownership(),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "business_ideas",
        sa.Column("id", sa.String(), primary_key=True), *ownership(),
        sa.Column("facts_json", sa.Text(), nullable=False),
        sa.Column("plans_json", sa.Text(), nullable=False),
        sa.Column("selected_plan", sa.String(30), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "idea_revisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("idea_id", sa.String(), sa.ForeignKey("business_ideas.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("facts_json", sa.Text(), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idea_id", "version", name="uq_idea_revision"),
    )
    op.create_index("ix_idea_revisions_idea_id", "idea_revisions", ["idea_id"])
    op.create_table(
        "business_projects",
        sa.Column("id", sa.String(), primary_key=True), *ownership(),
        sa.Column("idea_id", sa.String(), sa.ForeignKey("business_ideas.id"), nullable=False, unique=True),
        sa.Column("business_id", sa.String(), sa.ForeignKey("businesses.id"), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("plan_json", sa.Text(), nullable=False),
        sa.Column("budget_cents", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table in ("consultation_privacy", "business_ideas", "business_projects"):
        for column in ("tenant_id", "user_id"):
            op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade():
    db = op.get_bind()
    tables = ("business_projects", "idea_revisions", "business_ideas", "consultation_privacy")
    if any(db.scalar(sa.text(f"SELECT COUNT(*) FROM {table}")) for table in tables):
        raise RuntimeError("Refusing to remove saved ideas, projects or privacy decisions")
    for table in tables:
        op.drop_table(table)
