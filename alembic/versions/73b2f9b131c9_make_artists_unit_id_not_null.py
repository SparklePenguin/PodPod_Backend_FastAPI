"""make artists.unit_id not null

Revision ID: 73b2f9b131c9
Revises: b5614811adb0
Create Date: 2025-09-09 23:25:54.567120

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "73b2f9b131c9"
down_revision = "b5614811adb0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NULL unit_id 보정 (가능하면 blip_unit_id로 채움)
    try:
        op.execute(
            "UPDATE artists SET unit_id = blip_unit_id WHERE unit_id IS NULL AND blip_unit_id IS NOT NULL"
        )
    except Exception:
        pass
    # NOT NULL 강제
    try:
        op.alter_column(
            "artists", "unit_id", existing_type=sa.Integer(), nullable=False
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.alter_column("artists", "unit_id", existing_type=sa.Integer(), nullable=True)
    except Exception:
        pass
