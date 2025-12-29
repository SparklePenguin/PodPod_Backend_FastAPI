"""enforce not null on artists ids and cleanup defaults

Revision ID: bbcedd433bd4
Revises: f8be8facf987
Create Date: 2025-09-09 22:14:23.064750

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bbcedd433bd4"
down_revision = "f8be8facf987"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) blip_unit_id가 0인 레코드를 unit_id 값으로 보정 (없으면 그대로 둠)
    op.execute(
        """
        UPDATE artists
        SET blip_unit_id = unit_id
        WHERE blip_unit_id = 0 AND unit_id IS NOT NULL
        """
    )

    # 2) artists.blip_unit_id 기본값 제거 (남아있을 경우)
    try:
        op.alter_column("artists", "blip_unit_id", server_default=None)
    except Exception:
        pass

    # 3) NOT NULL 강제
    try:
        op.alter_column(
            "artists", "unit_id", existing_type=sa.Integer(), nullable=False
        )
    except Exception:
        pass
    try:
        op.alter_column(
            "artists", "blip_artist_id", existing_type=sa.Integer(), nullable=False
        )
    except Exception:
        pass
    try:
        op.alter_column(
            "artists", "blip_unit_id", existing_type=sa.Integer(), nullable=False
        )
    except Exception:
        pass


def downgrade() -> None:
    # NOT NULL 해제 (원복)
    try:
        op.alter_column(
            "artists", "blip_unit_id", existing_type=sa.Integer(), nullable=True
        )
    except Exception:
        pass
    try:
        op.alter_column(
            "artists", "blip_artist_id", existing_type=sa.Integer(), nullable=True
        )
    except Exception:
        pass
    try:
        op.alter_column("artists", "unit_id", existing_type=sa.Integer(), nullable=True)
    except Exception:
        pass
