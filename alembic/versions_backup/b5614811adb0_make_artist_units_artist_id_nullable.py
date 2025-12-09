"""make artist_units.artist_id nullable

Revision ID: b5614811adb0
Revises: 835a1899150f
Create Date: 2025-09-09 23:25:05.210092

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b5614811adb0"
down_revision = "835a1899150f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.alter_column(
            "artist_units",
            "artist_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.alter_column(
            "artist_units",
            "artist_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
    except Exception:
        pass
