"""remove_deprecated_columns_from_pods

Revision ID: 003
Revises: a1b2c3d4e5f6
Create Date: 2026-01-08 23:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    pods 테이블에서 pod_details로 이동한 컬럼들 삭제
    pod_details 테이블에서 deprecated 컬럼 삭제
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. pods 테이블에서 pod_details로 이동한 컬럼들 삭제
    if "pods" in inspector.get_table_names():
        pod_columns = [col["name"] for col in inspector.get_columns("pods")]

        # description 컬럼 삭제
        if "description" in pod_columns:
            op.drop_column("pods", "description")

        # image_url 컬럼 삭제
        if "image_url" in pod_columns:
            op.drop_column("pods", "image_url")

        # address 컬럼 삭제
        if "address" in pod_columns:
            op.drop_column("pods", "address")

        # sub_address 컬럼 삭제
        if "sub_address" in pod_columns:
            op.drop_column("pods", "sub_address")

        # x 컬럼 삭제 (경도)
        if "x" in pod_columns:
            op.drop_column("pods", "x")

        # y 컬럼 삭제 (위도)
        if "y" in pod_columns:
            op.drop_column("pods", "y")

    # 2. pod_details 테이블에서 deprecated 컬럼 삭제
    if "pod_details" in inspector.get_table_names():
        pod_detail_columns = [col["name"] for col in inspector.get_columns("pod_details")]

        # chat_channel_url 컬럼 삭제 (deprecated - chat_room_id 사용)
        if "chat_channel_url" in pod_detail_columns:
            op.drop_column("pod_details", "chat_channel_url")


def downgrade() -> None:
    """
    삭제한 컬럼들을 다시 추가 (롤백)
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. pods 테이블에 컬럼 다시 추가
    if "pods" in inspector.get_table_names():
        pod_columns = [col["name"] for col in inspector.get_columns("pods")]

        # y 컬럼 추가 (위도) - 역순으로 추가
        if "y" not in pod_columns:
            op.add_column(
                "pods",
                sa.Column("y", sa.Float(), nullable=True, comment="위도 (latitude)"),
            )

        # x 컬럼 추가 (경도)
        if "x" not in pod_columns:
            op.add_column(
                "pods",
                sa.Column("x", sa.Float(), nullable=True, comment="경도 (longitude)"),
            )

        # sub_address 컬럼 추가
        if "sub_address" not in pod_columns:
            op.add_column(
                "pods",
                sa.Column("sub_address", sa.String(300), nullable=True, comment="상세 주소"),
            )

        # address 컬럼 추가
        if "address" not in pod_columns:
            op.add_column(
                "pods",
                sa.Column("address", sa.String(300), nullable=True, comment="주소"),
            )

        # image_url 컬럼 추가
        if "image_url" not in pod_columns:
            op.add_column(
                "pods",
                sa.Column("image_url", sa.String(500), nullable=True, comment="이미지 URL"),
            )

        # description 컬럼 추가
        if "description" not in pod_columns:
            op.add_column(
                "pods",
                sa.Column("description", sa.String(500), nullable=True, comment="파티 설명"),
            )

    # 2. pod_details 테이블에 컬럼 다시 추가
    if "pod_details" in inspector.get_table_names():
        pod_detail_columns = [col["name"] for col in inspector.get_columns("pod_details")]

        # chat_channel_url 컬럼 추가
        if "chat_channel_url" not in pod_detail_columns:
            op.add_column(
                "pod_details",
                sa.Column(
                    "chat_channel_url",
                    sa.String(255),
                    nullable=True,
                    comment="채팅방 URL (deprecated - Pod.chat_room_id 사용)",
                ),
            )
