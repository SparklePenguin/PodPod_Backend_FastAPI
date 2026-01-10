"""remove_channel_url_from_chat_messages

Revision ID: 005
Revises: 004
Create Date: 2026-01-09 03:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    chat_messages 테이블에서 channel_url 컬럼 완전 삭제
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chat_messages" in inspector.get_table_names():
        chat_message_columns = [col["name"] for col in inspector.get_columns("chat_messages")]

        # channel_url 컬럼 삭제 (deprecated - chat_room_id 사용)
        if "channel_url" in chat_message_columns:
            op.drop_column("chat_messages", "channel_url")


def downgrade() -> None:
    """
    channel_url 컬럼 다시 추가
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chat_messages" in inspector.get_table_names():
        chat_message_columns = [col["name"] for col in inspector.get_columns("chat_messages")]

        # channel_url 컬럼 다시 추가
        if "channel_url" not in chat_message_columns:
            op.add_column(
                "chat_messages",
                sa.Column(
                    "channel_url",
                    sa.String(255),
                    nullable=True,
                    comment="채널 URL (deprecated - chat_room_id 사용)",
                ),
            )
