"""Add fail-closed, simulated financial controls without enabling a provider."""
from alembic import op
from app.models import AICostPolicy, AIBudgetBucket, AICostReservation
revision = "g0010"
down_revision = "g0009"
branch_labels = None
depends_on = None


def upgrade():
    for model in (AICostPolicy, AIBudgetBucket, AICostReservation):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError("Financial audit/reservation retention requires explicit review; no automatic deletion")
