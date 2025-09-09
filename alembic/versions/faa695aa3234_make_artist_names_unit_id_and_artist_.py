"""make artist_names.unit_id and artist_images.unit_id not null; fix name column

Revision ID: faa695aa3234
Revises: 73b2f9b131c9
Create Date: 2025-09-09 23:27:26.656038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'faa695aa3234'
down_revision = '73b2f9b131c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
