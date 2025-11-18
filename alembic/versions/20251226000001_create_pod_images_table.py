"""create_pod_images_table

Revision ID: 20251226000001
Revises: 20251011000004
Create Date: 2025-12-26 00:00:01.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20251226000001"
down_revision = "20251011000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pod_images 테이블 생성
    op.create_table(
        "pod_images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "pod_id",
            sa.Integer(),
            nullable=False,
            comment="파티 ID",
        ),
        sa.Column(
            "image_url",
            sa.String(length=500),
            nullable=False,
            comment="이미지 URL",
        ),
        sa.Column(
            "thumbnail_url",
            sa.String(length=500),
            nullable=True,
            comment="썸네일 URL",
        ),
        sa.Column(
            "display_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="표시 순서",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            comment="생성 일시",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["pod_id"],
            ["pods.id"],
            ondelete="CASCADE",
        ),
    )

    # 인덱스 생성
    op.create_index(
        op.f("ix_pod_images_id"),
        "pod_images",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pod_images_pod_id"),
        "pod_images",
        ["pod_id"],
        unique=False,
    )

    # 기존 pods 테이블의 image_url 데이터를 pod_images로 마이그레이션
    connection = op.get_bind()
    
    # pods 테이블에서 image_url과 thumbnail_url이 있는 데이터를 조회
    result = connection.execute(
        text("""
            SELECT id, image_url, thumbnail_url 
            FROM pods 
            WHERE image_url IS NOT NULL AND image_url != ''
        """)
    )
    
    # 각 파티의 기존 이미지를 pod_images 테이블에 삽입
    for row in result:
        pod_id = row[0]
        image_url = row[1]
        thumbnail_url = row[2] if row[2] else None
        
        connection.execute(
            text("""
                INSERT INTO pod_images (pod_id, image_url, thumbnail_url, display_order, created_at)
                VALUES (:pod_id, :image_url, :thumbnail_url, 0, NOW())
            """),
            {"pod_id": pod_id, "image_url": image_url, "thumbnail_url": thumbnail_url}
        )


def downgrade() -> None:
    # 인덱스 삭제
    op.drop_index(op.f("ix_pod_images_pod_id"), table_name="pod_images")
    op.drop_index(op.f("ix_pod_images_id"), table_name="pod_images")
    
    # 테이블 삭제
    op.drop_table("pod_images")
