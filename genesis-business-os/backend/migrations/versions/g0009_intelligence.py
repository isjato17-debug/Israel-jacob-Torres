"""Add isolated, versioned mock/provider proposal records; preserve all prior tables."""
from alembic import op
from app.models import IntelligenceRecord

revision = "g0009"
down_revision = "g0008"
branch_labels = None
depends_on = None


def upgrade():
    IntelligenceRecord.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    # Never silently delete customer proposals in an automated downgrade.
    raise RuntimeError("Intelligence history requires an explicitly reviewed retention/export procedure")
