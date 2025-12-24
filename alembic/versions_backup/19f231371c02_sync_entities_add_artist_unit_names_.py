"""sync entities: add artist unit/names/images and artist fields

Revision ID: 19f231371c02
Revises: 5d63b2c4df9c
Create Date: 2025-09-09 21:19:55.877008

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "19f231371c02"
down_revision = "5d63b2c4df9c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # artists 테이블 보정: blip_unit_id 추가 (+ 인덱스)
    try:
        op.add_column(
            "artists",
            sa.Column("blip_unit_id", sa.Integer(), nullable=True, server_default="0"),
        )
        op.alter_column("artists", "blip_unit_id", server_default=None, nullable=False)
        op.create_index(
            op.f("ix_artists_blip_unit_id"), "artists", ["blip_unit_id"], unique=False
        )
    except Exception:
        # 컬럼이 이미 존재하는 경우를 허용
        pass

    # artist_units 테이블 생성 (이미 존재하면 스킵)
    try:
        op.create_table(
            "artist_units",
            sa.Column(
                "id", sa.Integer(), primary_key=True, autoincrement=True, index=True
            ),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("artist_id", sa.Integer(), nullable=False, index=True),
            sa.Column("blip_unit_id", sa.Integer(), nullable=False, index=True),
            sa.Column("blip_artist_id", sa.Integer(), nullable=False, index=True),
            sa.Column("type", sa.String(length=20), nullable=True),
            sa.Column(
                "is_filter", sa.Boolean(), nullable=False, server_default=sa.text("1")
            ),
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["artist_id"],
                ["artists.id"],
            ),
            mysql_engine="InnoDB",
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
        )
    except Exception:
        pass
    # artist_units.artist_id는 Column 선언에서 index=True 처리됨 (중복 인덱스 생성 방지)

    # artist_images 테이블 생성
    op.create_table(
        "artist_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column("artist_id", sa.Integer(), nullable=False, index=True),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("file_id", sa.String(length=100), nullable=True),
        sa.Column(
            "is_animatable", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("size", sa.String(length=50), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    # artist_images.artist_id는 Column 선언에서 index=True 처리됨 (중복 인덱스 생성 방지)
    op.create_index(
        op.f("ix_artist_images_unit_id"), "artist_images", ["unit_id"], unique=False
    )

    # artist_names 테이블 생성
    op.create_table(
        "artist_names",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
        sa.Column("artist_id", sa.Integer(), nullable=False, index=True),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    # artist_names.artist_id는 Column 선언에서 index=True 처리됨 (중복 인덱스 생성 방지)
    op.create_index(
        op.f("ix_artist_names_unit_id"), "artist_names", ["unit_id"], unique=False
    )


def downgrade() -> None:
    # artist_names / artist_images / artist_units 제거
    op.drop_index(op.f("ix_artist_names_unit_id"), table_name="artist_names")
    op.drop_index(op.f("ix_artist_names_artist_id"), table_name="artist_names")
    op.drop_table("artist_names")

    op.drop_index(op.f("ix_artist_images_unit_id"), table_name="artist_images")
    op.drop_index(op.f("ix_artist_images_artist_id"), table_name="artist_images")
    op.drop_table("artist_images")

    op.drop_index(op.f("ix_artist_units_artist_id"), table_name="artist_units")
    op.drop_table("artist_units")

    # artists 보정 롤백: blip_unit_id 제거
    try:
        op.drop_index(op.f("ix_artists_blip_unit_id"), table_name="artists")
        op.drop_column("artists", "blip_unit_id")
    except Exception:
        pass
