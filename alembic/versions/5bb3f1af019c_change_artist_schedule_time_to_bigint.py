"""change_artist_schedule_time_to_bigint

Revision ID: 5bb3f1af019c
Revises: 001
Create Date: 2025-12-09 11:59:53.364928

"""
from alembic import op  # type: ignore
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bb3f1af019c'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # start_time과 end_time을 INT에서 BIGINT로 변경
    op.alter_column('artist_schedules', 'start_time',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)

    op.alter_column('artist_schedules', 'end_time',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    # BIGINT에서 INT로 되돌리기
    op.alter_column('artist_schedules', 'start_time',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)

    op.alter_column('artist_schedules', 'end_time',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
