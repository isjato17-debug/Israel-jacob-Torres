"""Private funding profiles and immutable preparation revisions; never official submissions."""
from alembic import op
from app.models import FundingProfile, FundingApplication
revision = "g0011"
down_revision = "g0010"
branch_labels = None
depends_on = None


def upgrade():
    for model in (FundingProfile, FundingApplication):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError("Sensitive funding records require an explicitly reviewed retention/export procedure")
