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
    # SQLite에서는 ALTER COLUMN을 지원하지 않으므로 테이블을 재생성해야 함
    
    # 1. 기존 데이터 백업을 위한 임시 테이블 생성
    op.execute("""
        CREATE TABLE users_backup AS 
        SELECT id, username, email, nickname, intro, hashed_password, 
               profile_image, is_active, created_at, updated_at, 
               auth_provider, auth_provider_id,
               CASE 
                   WHEN needs_onboarding = 1 THEN 'PREFERRED_ARTISTS'
                   ELSE 'COMPLETED'
               END as state
        FROM users
    """)
    
    # 2. 기존 users 테이블 삭제
    op.drop_table('users')
    
    # 3. 새로운 users 테이블 생성 (state 컬럼 포함)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('intro', sa.String(length=200), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('profile_image', sa.String(length=500), nullable=True),
        sa.Column('state', sa.Enum('PREFERRED_ARTISTS', 'TENDENCY_TEST', 'PROFILE_SETTING', 'COMPLETED', name='userstate'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('auth_provider', sa.String(length=20), nullable=True),
        sa.Column('auth_provider_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. 인덱스 재생성
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_auth_provider_id'), 'users', ['auth_provider_id'], unique=True)
    
    # 5. 백업 데이터를 새 테이블로 복사
    op.execute("""
        INSERT INTO users (id, username, email, nickname, intro, hashed_password, 
                          profile_image, state, is_active, created_at, updated_at, 
                          auth_provider, auth_provider_id)
        SELECT id, username, email, nickname, intro, hashed_password, 
               profile_image, state, is_active, created_at, updated_at, 
               auth_provider, auth_provider_id
        FROM users_backup
    """)
    
    # 6. 백업 테이블 삭제
    op.drop_table('users_backup')


def downgrade() -> None:
    # SQLite에서는 ALTER COLUMN을 지원하지 않으므로 테이블을 재생성해야 함
    
    # 1. 기존 데이터 백업을 위한 임시 테이블 생성
    op.execute("""
        CREATE TABLE users_backup AS 
        SELECT id, username, email, nickname, intro, hashed_password, 
               profile_image, is_active, created_at, updated_at, 
               auth_provider, auth_provider_id,
               CASE 
                   WHEN state = 'COMPLETED' THEN 0
                   ELSE 1
               END as needs_onboarding
        FROM users
    """)
    
    # 2. 기존 users 테이블 삭제
    op.drop_table('users')
    
    # 3. 새로운 users 테이블 생성 (needs_onboarding 컬럼 포함)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('intro', sa.String(length=200), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('profile_image', sa.String(length=500), nullable=True),
        sa.Column('needs_onboarding', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('auth_provider', sa.String(length=20), nullable=True),
        sa.Column('auth_provider_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. 인덱스 재생성
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_auth_provider_id'), 'users', ['auth_provider_id'], unique=True)
    
    # 5. 백업 데이터를 새 테이블로 복사
    op.execute("""
        INSERT INTO users (id, username, email, nickname, intro, hashed_password, 
                          profile_image, needs_onboarding, is_active, created_at, updated_at, 
                          auth_provider, auth_provider_id)
        SELECT id, username, email, nickname, intro, hashed_password, 
               profile_image, needs_onboarding, is_active, created_at, updated_at, 
               auth_provider, auth_provider_id
        FROM users_backup
    """)
    
    # 6. 백업 테이블 삭제
    op.drop_table('users_backup')
