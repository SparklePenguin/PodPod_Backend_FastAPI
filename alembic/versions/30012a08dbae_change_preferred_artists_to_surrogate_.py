"""change preferred_artists to surrogate pk with id and fks on user_id, artist_id

Revision ID: 30012a08dbae
Revises: faa695aa3234
Create Date: 2025-09-10 00:07:58.478514

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "30012a08dbae"
down_revision = "faa695aa3234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) 기존 PK 드롭 (복합 PK)
    try:
        op.drop_constraint("PRIMARY", "preferred_artists", type_="primary")
    except Exception:
        pass

    # 2) id 컬럼 추가 및 PK 설정
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

    # 3) user_id / artist_id NOT NULL 및 인덱스 보장
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

    # 4) FK 복구
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
    for fk in ["fk_preferred_artists_artist_id", "fk_preferred_artists_user_id"]:
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

    # PK 원복: id PK 제거, 복합 PK 복구
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
