"""add_last_read_at_to_chat_members

Revision ID: f46a099880f5
Revises: 6cc4f2af020d
Create Date: 2026-01-04 20:48:48.584496

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f46a099880f5'
down_revision = '6cc4f2af020d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """chat_members 테이블에 last_read_at 컬럼 추가"""
    # 테이블 존재 여부 및 컬럼 존재 여부 확인
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'chat_members' in inspector.get_table_names():
        chat_member_columns = [col['name'] for col in inspector.get_columns('chat_members')]
        if 'last_read_at' not in chat_member_columns:
            op.add_column(
                'chat_members',
                sa.Column(
                    'last_read_at',
                    sa.DateTime(),
                    nullable=True,
                    comment='마지막 읽은 시간 (읽지 않은 메시지 수 계산용)'
                )
            )


def downgrade() -> None:
    """chat_members 테이블에서 last_read_at 컬럼 제거"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'chat_members' in inspector.get_table_names():
        chat_member_columns = [col['name'] for col in inspector.get_columns('chat_members')]
        if 'last_read_at' in chat_member_columns:
            op.drop_column('chat_members', 'last_read_at')
