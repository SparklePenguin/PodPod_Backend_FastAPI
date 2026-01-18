"""change datetime columns from int to datetime

Revision ID: 002
Revises: f46a099880f5
Create Date: 2026-01-06 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = 'f46a099880f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """INT 타입의 datetime 컬럼들을 DATETIME 타입으로 변경"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # pod_applications 테이블 처리
    if 'pod_applications' in inspector.get_table_names():
        columns = {col['name']: col for col in inspector.get_columns('pod_applications')}
        
        # applied_at: INT -> DATETIME
        if 'applied_at' in columns:
            op.alter_column('pod_applications', 'applied_at',
                          existing_type=sa.Integer(),
                          type_=sa.DateTime(),
                          existing_nullable=False)
        
        # reviewed_at: INT -> DATETIME
        if 'reviewed_at' in columns:
            op.alter_column('pod_applications', 'reviewed_at',
                          existing_type=sa.Integer(),
                          type_=sa.DateTime(),
                          existing_nullable=True)
    
    # pod_members 테이블 처리
    if 'pod_members' in inspector.get_table_names():
        columns = {col['name']: col for col in inspector.get_columns('pod_members')}
        
        # joined_at: INT -> DATETIME
        if 'joined_at' in columns:
            op.alter_column('pod_members', 'joined_at',
                          existing_type=sa.Integer(),
                          type_=sa.DateTime(),
                          existing_nullable=False)


def downgrade() -> None:
    """DATETIME 타입을 INT 타입으로 되돌리기"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # pod_applications 테이블 처리
    if 'pod_applications' in inspector.get_table_names():
        columns = {col['name']: col for col in inspector.get_columns('pod_applications')}
        
        # applied_at: DATETIME -> INT
        if 'applied_at' in columns:
            op.alter_column('pod_applications', 'applied_at',
                          existing_type=sa.DateTime(),
                          type_=sa.Integer(),
                          existing_nullable=False)
        
        # reviewed_at: DATETIME -> INT
        if 'reviewed_at' in columns:
            op.alter_column('pod_applications', 'reviewed_at',
                          existing_type=sa.DateTime(),
                          type_=sa.Integer(),
                          existing_nullable=True)
    
    # pod_members 테이블 처리
    if 'pod_members' in inspector.get_table_names():
        columns = {col['name']: col for col in inspector.get_columns('pod_members')}
        
        # joined_at: DATETIME -> INT
        if 'joined_at' in columns:
            op.alter_column('pod_members', 'joined_at',
                          existing_type=sa.DateTime(),
                          type_=sa.Integer(),
                          existing_nullable=False)
