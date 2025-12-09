"""merge_all_heads

Revision ID: 9259d44244fe
Revises: 20251119000000, 20251226000001, 8f72471946fc, a1b2c3d4e5f6, y44fd96f85b9
Create Date: 2025-12-09 11:47:12.980089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9259d44244fe'
down_revision = ('20251119000000', '20251226000001', '8f72471946fc', 'a1b2c3d4e5f6', 'y44fd96f85b9')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
