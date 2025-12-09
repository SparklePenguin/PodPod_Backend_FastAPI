"""Add user state enum and update schema

Revision ID: 2916265d454a
Revises: 
Create Date: 2025-09-05 02:00:05.624206

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2916265d454a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL에서는 ALTER COLUMN을 지원하므로 더 간단하게 처리 가능
    
    # 1. UserState ENUM 타입 생성
    userstate_enum = sa.Enum('PREFERRED_ARTISTS', 'TENDENCY_TEST', 'PROFILE_SETTING', 'COMPLETED', name='userstate')
    userstate_enum.create(op.get_bind())
    
    # 2. state 컬럼 추가 (기본값: PREFERRED_ARTISTS)
    op.add_column('users', sa.Column('state', userstate_enum, nullable=False, server_default='PREFERRED_ARTISTS'))
    
    # 3. 기존 데이터의 state 값 업데이트 (needs_onboarding 컬럼이 있다면)
    # MySQL에서는 컬럼 존재 여부를 확인하고 업데이트
    op.execute("""
        UPDATE users 
        SET state = CASE 
            WHEN needs_onboarding = 1 THEN 'PREFERRED_ARTISTS'
            ELSE 'COMPLETED'
        END
        WHERE needs_onboarding IS NOT NULL
    """)
    
    # 4. needs_onboarding 컬럼 제거 (존재한다면)
    # MySQL에서는 컬럼 존재 여부를 확인하고 삭제
    try:
        op.drop_column('users', 'needs_onboarding')
    except Exception:
        # 컬럼이 존재하지 않으면 무시
        pass


def downgrade() -> None:
    # MySQL에서는 ALTER COLUMN을 지원하므로 더 간단하게 처리 가능
    
    # 1. needs_onboarding 컬럼 추가
    op.add_column('users', sa.Column('needs_onboarding', sa.Boolean(), nullable=False, server_default='1'))
    
    # 2. 기존 데이터의 needs_onboarding 값 업데이트
    op.execute("""
        UPDATE users 
        SET needs_onboarding = CASE 
            WHEN state = 'COMPLETED' THEN 0
            ELSE 1
        END
    """)
    
    # 3. state 컬럼 제거
    op.drop_column('users', 'state')
    
    # 4. UserState ENUM 타입 삭제
    userstate_enum = sa.Enum(name='userstate')
    userstate_enum.drop(op.get_bind())
