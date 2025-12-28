"""add artist.type column

Revision ID: 5d63b2c4df9c
Revises: x43fd96f85b9
Create Date: 2025-09-09 18:48:25.622328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d63b2c4df9c'
down_revision = 'x43fd96f85b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL용: VARCHAR(20) 컬럼 추가 (nullable)
    op.add_column('artists', sa.Column('type', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('artists', 'type')
