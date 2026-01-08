"""fix_chat_messages_columns

Revision ID: 004
Revises: 003
Create Date: 2026-01-09 02:40:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    chat_messages 테이블 컬럼 수정
    - channel_url: nullable=True (deprecated - chat_room_id 사용)
    - chat_room_id: nullable=False (필수)
    - message_type: Enum 타입으로 변경
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chat_messages" in inspector.get_table_names():
        # 1. channel_url을 nullable로 변경 (deprecated)
        op.alter_column(
            "chat_messages",
            "channel_url",
            existing_type=sa.String(255),
            nullable=True,
            existing_nullable=False,
            comment="채널 URL (deprecated - chat_room_id 사용)",
        )

        # 2. chat_room_id를 NOT NULL로 변경 (필수)
        # 먼저 NULL 값이 있는지 확인하고 업데이트
        op.execute(
            """
            UPDATE chat_messages
            SET chat_room_id = (
                SELECT id FROM chat_rooms
                WHERE CONCAT('chat_room_', id) = chat_messages.channel_url
                LIMIT 1
            )
            WHERE chat_room_id IS NULL AND channel_url IS NOT NULL
            """
        )

        op.alter_column(
            "chat_messages",
            "chat_room_id",
            existing_type=sa.Integer(),
            nullable=False,
            existing_nullable=True,
            comment="채팅방 ID",
        )

        # 3. message_type을 Enum으로 변경
        # 기존 데이터 확인 후 변경
        op.execute(
            """
            UPDATE chat_messages
            SET message_type = 'TEXT'
            WHERE message_type NOT IN ('TEXT', 'FILE', 'IMAGE', 'SYSTEM')
            """
        )

        op.alter_column(
            "chat_messages",
            "message_type",
            existing_type=sa.String(20),
            type_=sa.Enum("TEXT", "FILE", "IMAGE", "SYSTEM", name="messagetype"),
            nullable=False,
            existing_nullable=False,
            comment="메시지 타입 (TEXT, FILE, IMAGE, SYSTEM)",
        )


def downgrade() -> None:
    """
    원래대로 되돌리기
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chat_messages" in inspector.get_table_names():
        # 1. message_type을 String으로 변경
        op.alter_column(
            "chat_messages",
            "message_type",
            existing_type=sa.Enum("TEXT", "FILE", "IMAGE", "SYSTEM", name="messagetype"),
            type_=sa.String(20),
            nullable=False,
            existing_nullable=False,
        )

        # 2. chat_room_id를 nullable로 변경
        op.alter_column(
            "chat_messages",
            "chat_room_id",
            existing_type=sa.Integer(),
            nullable=True,
            existing_nullable=False,
        )

        # 3. channel_url을 NOT NULL로 변경
        # NULL 값을 기본값으로 채우기
        op.execute(
            """
            UPDATE chat_messages
            SET channel_url = CONCAT('chat_room_', chat_room_id)
            WHERE channel_url IS NULL
            """
        )

        op.alter_column(
            "chat_messages",
            "channel_url",
            existing_type=sa.String(255),
            nullable=False,
            existing_nullable=True,
        )
