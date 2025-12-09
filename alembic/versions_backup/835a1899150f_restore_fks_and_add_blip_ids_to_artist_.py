"""restore fks and add blip ids to artist_images and names

Revision ID: 835a1899150f
Revises: bbcedd433bd4
Create Date: 2025-09-09 23:23:05.187043

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "835a1899150f"
down_revision = "bbcedd433bd4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) artist_images / artist_names에 blip 식별자 컬럼 추가 (없을 때만)
    try:
        op.add_column(
            "artist_images", sa.Column("blip_unit_id", sa.Integer(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column(
            "artist_images", sa.Column("blip_artist_id", sa.Integer(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_artist_images_blip_unit_id"),
            "artist_images",
            ["blip_unit_id"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_artist_images_blip_artist_id"),
            "artist_images",
            ["blip_artist_id"],
            unique=False,
        )
    except Exception:
        pass

    try:
        op.add_column(
            "artist_names", sa.Column("blip_unit_id", sa.Integer(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.add_column(
            "artist_names", sa.Column("blip_artist_id", sa.Integer(), nullable=True)
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_artist_names_blip_unit_id"),
            "artist_names",
            ["blip_unit_id"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            op.f("ix_artist_names_blip_artist_id"),
            "artist_names",
            ["blip_artist_id"],
            unique=False,
        )
    except Exception:
        pass

    # 2) FK 복구: artist_images/artist_names/artist_units → artists, preferred_artists → users/artists
    try:
        op.create_foreign_key(
            "fk_artist_images_artist_id",
            "artist_images",
            "artists",
            ["artist_id"],
            ["id"],
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            "fk_artist_names_artist_id",
            "artist_names",
            "artists",
            ["artist_id"],
            ["id"],
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            "fk_artist_units_artist_id",
            "artist_units",
            "artists",
            ["artist_id"],
            ["id"],
        )
    except Exception:
        pass
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
    for tbl, fk in [
        ("preferred_artists", "fk_preferred_artists_artist_id"),
        ("preferred_artists", "fk_preferred_artists_user_id"),
        ("artist_units", "fk_artist_units_artist_id"),
        ("artist_names", "fk_artist_names_artist_id"),
        ("artist_images", "fk_artist_images_artist_id"),
    ]:
        try:
            op.drop_constraint(fk, tbl, type_="foreignkey")
        except Exception:
            pass

    # 인덱스/컬럼 제거
    for tbl, col, idx in [
        ("artist_names", "blip_artist_id", op.f("ix_artist_names_blip_artist_id")),
        ("artist_names", "blip_unit_id", op.f("ix_artist_names_blip_unit_id")),
        ("artist_images", "blip_artist_id", op.f("ix_artist_images_blip_artist_id")),
        ("artist_images", "blip_unit_id", op.f("ix_artist_images_blip_unit_id")),
    ]:
        try:
            # drop index if exists
            op.drop_index(idx, table_name=tbl)
        except Exception:
            pass
        try:
            op.drop_column(tbl, col)
        except Exception:
            pass
