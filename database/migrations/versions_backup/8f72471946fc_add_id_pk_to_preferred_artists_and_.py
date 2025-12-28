"""add id pk to preferred_artists and restore fks

Revision ID: 8f72471946fc
Revises: 30012a08dbae
Create Date: 2025-09-10 01:24:33.104921

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f72471946fc"
down_revision = "30012a08dbae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 기존 복합 PK 제거
    try:
        op.drop_constraint("PRIMARY", "preferred_artists", type_="primary")
    except Exception:
        pass

    # id 컬럼 추가 및 PK 설정
    try:
        op.add_column(
            "preferred_artists",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        )
    except Exception:
        pass
    try:
        op.create_primary_key("pk_preferred_artists_id", "preferred_artists", ["id"])
    except Exception:
        pass

    # user_id / artist_id NOT NULL + 인덱스
    try:
        op.alter_column(
            "preferred_artists", "user_id", existing_type=sa.Integer(), nullable=False
        )
    except Exception:
        pass
    try:
        op.alter_column(
            "preferred_artists", "artist_id", existing_type=sa.Integer(), nullable=False
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_preferred_artists_user_id"),
            "preferred_artists",
            ["user_id"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_preferred_artists_artist_id"),
            "preferred_artists",
            ["artist_id"],
            unique=False,
        )
    except Exception:
        pass

    # FK 복구
    try:
        op.create_foreign_key(
            "fk_preferred_artists_user_id",
            "preferred_artists",
            "users",
            ["user_id"],
            ["id"],
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            "fk_preferred_artists_artist_id",
            "preferred_artists",
            "artists",
            ["artist_id"],
            ["id"],
        )
    except Exception:
        pass


def downgrade() -> None:
    # FK 제거
    for fk in [
        "fk_preferred_artists_artist_id",
        "fk_preferred_artists_user_id",
    ]:
        try:
            op.drop_constraint(fk, "preferred_artists", type_="foreignkey")
        except Exception:
            pass

    # 인덱스 제거
    for idx in [
        op.f("ix_preferred_artists_artist_id"),
        op.f("ix_preferred_artists_user_id"),
    ]:
        try:
            op.drop_index(idx, table_name="preferred_artists")
        except Exception:
            pass

    # PK 원복
    try:
        op.drop_constraint(
            "pk_preferred_artists_id", "preferred_artists", type_="primary"
        )
    except Exception:
        pass
    try:
        op.drop_column("preferred_artists", "id")
    except Exception:
        pass
    try:
        op.create_primary_key("PRIMARY", "preferred_artists", ["user_id", "artist_id"])
    except Exception:
        pass
