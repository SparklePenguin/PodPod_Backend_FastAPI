"""Initial migration for MySQL

Revision ID: c3d2e62dc28d
Revises: 2916265d454a
Create Date: 2025-09-06 20:08:31.287314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d2e62dc28d'
down_revision = '2916265d454a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL 마이그레이션을 위한 빈 마이그레이션
    # 실제 테이블 생성은 SQLAlchemy의 create_all()에서 처리됨
    pass


def downgrade() -> None:
    # MySQL 마이그레이션을 위한 빈 마이그레이션
    pass
