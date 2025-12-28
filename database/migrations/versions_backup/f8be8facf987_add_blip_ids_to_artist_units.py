"""add blip ids to artist_units

Revision ID: f8be8facf987
Revises: 19f231371c02
Create Date: 2025-09-09 21:50:12.268292

"""

import sqlalchemy as sa

from alembic import op 

# revision identifiers, used by Alembic.
revision = "f8be8facf987"
down_revision = "19f231371c02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # artist_units 테이블에 blip_unit_id, blip_artist_id 추가 (없을 때만)
    try:
        op.add_column(
            "artist_units", sa.Column("blip_unit_id", sa.Integer(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column(
            "artist_units", sa.Column("blip_artist_id", sa.Integer(), nullable=True)
        )
    except Exception:
        pass

    # 인덱스 추가 (중복 생성 방지)
    try:
        op.create_index(
            op.f("ix_artist_units_blip_unit_id"),
            "artist_units",
            ["blip_unit_id"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_artist_units_blip_artist_id"),
            "artist_units",
            ["blip_artist_id"],
            unique=False,
        )
    except Exception:
        pass


def downgrade() -> None:
    # 인덱스/컬럼 제거 (존재할 때만)
    try:
        op.drop_index(op.f("ix_artist_units_blip_artist_id"), table_name="artist_units")
    except Exception:
        pass
    try:
        op.drop_index(op.f("ix_artist_units_blip_unit_id"), table_name="artist_units")
    except Exception:
        pass
    try:
        op.drop_column("artist_units", "blip_artist_id")
    except Exception:
        pass
    try:
        op.drop_column("artist_units", "blip_unit_id")
    except Exception:
        pass
