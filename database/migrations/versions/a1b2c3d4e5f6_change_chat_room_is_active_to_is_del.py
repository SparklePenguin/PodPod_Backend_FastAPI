"""change_chat_room_is_active_to_is_del

Revision ID: a1b2c3d4e5f6
Revises: 002
Create Date: 2026-01-20 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """chat_rooms 테이블의 is_active를 is_del로 변경"""
    # 테이블 존재 여부 및 컬럼 존재 여부 확인
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chat_rooms" in inspector.get_table_names():
        chat_room_columns = [col["name"] for col in inspector.get_columns("chat_rooms")]

        # 1. is_del 컬럼 추가 (기본값 True, nullable=False)
        if "is_del" not in chat_room_columns:
            op.add_column(
                "chat_rooms",
                sa.Column(
                    "is_del",
                    sa.Boolean(),
                    nullable=False,
                    server_default="1",
                    comment="활성화 여부",
                ),
            )

        # 2. 기존 is_active 값을 반전시켜서 is_del에 저장
        # is_active=True -> is_del=False (활성화됨 = 삭제 안됨)
        # is_active=False -> is_del=True (비활성화됨 = 삭제됨)
        if "is_active" in chat_room_columns:
            op.execute(
                "UPDATE chat_rooms SET is_del = NOT is_active WHERE is_active IS NOT NULL"
            )

        # 3. is_active 컬럼 제거
        if "is_active" in chat_room_columns:
            op.drop_column("chat_rooms", "is_active")


def downgrade() -> None:
    """chat_rooms 테이블의 is_del을 is_active로 되돌리기"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chat_rooms" in inspector.get_table_names():
        chat_room_columns = [col["name"] for col in inspector.get_columns("chat_rooms")]

        # 1. is_active 컬럼 추가
        if "is_active" not in chat_room_columns:
            op.add_column(
                "chat_rooms",
                sa.Column(
                    "is_active",
                    sa.Boolean(),
                    nullable=False,
                    server_default="1",
                    comment="활성화 여부",
                ),
            )

        # 2. is_del 값을 반전시켜서 is_active에 저장
        if "is_del" in chat_room_columns:
            op.execute(
                "UPDATE chat_rooms SET is_active = NOT is_del WHERE is_del IS NOT NULL"
            )

        # 3. is_del 컬럼 제거
        if "is_del" in chat_room_columns:
            op.drop_column("chat_rooms", "is_del")
