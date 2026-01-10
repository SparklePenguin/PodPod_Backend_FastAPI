"""split_user_to_user_detail

Revision ID: 006
Revises: 005
Create Date: 2026-01-10 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    User 테이블 분리:
    1. user_details 테이블 생성
    2. users 테이블에 tendency_type 컬럼 추가
    3. users 테이블의 데이터를 user_details로 마이그레이션
    4. user_tendency_results의 tendency_type을 users로 복사
    5. users 테이블에서 이동된 컬럼 삭제
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. user_details 테이블 생성
    if "user_details" not in existing_tables:
        op.create_table(
            "user_details",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                unique=True,
                nullable=False,
                index=True,
            ),
            sa.Column("username", sa.String(50), nullable=True),
            sa.Column("email", sa.String(100), nullable=True),
            sa.Column("fcm_token", sa.String(500), nullable=True),
            sa.Column("terms_accepted", sa.Boolean(), default=False, nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )

    # 2. users 테이블에 tendency_type 컬럼 추가
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "tendency_type" not in user_columns:
        op.add_column(
            "users",
            sa.Column("tendency_type", sa.String(50), nullable=True),
        )

    # 3. 기존 users 데이터를 user_details로 마이그레이션
    op.execute(
        """
        INSERT INTO user_details (user_id, username, email, fcm_token, terms_accepted, updated_at)
        SELECT id, username, email, fcm_token, COALESCE(terms_accepted, FALSE), updated_at
        FROM users
        WHERE id NOT IN (SELECT user_id FROM user_details)
        """
    )

    # 4. user_tendency_results의 tendency_type을 users로 복사
    if "user_tendency_results" in existing_tables:
        op.execute(
            """
            UPDATE users u
            SET tendency_type = (
                SELECT utr.tendency_type
                FROM user_tendency_results utr
                WHERE utr.user_id = u.id
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1 FROM user_tendency_results utr WHERE utr.user_id = u.id
            )
            """
        )

    # 5. users 테이블에서 이동된 컬럼 삭제
    columns_to_remove = ["username", "email", "fcm_token", "terms_accepted"]
    for col in columns_to_remove:
        if col in user_columns:
            op.drop_column("users", col)


def downgrade() -> None:
    """
    롤백:
    1. users 테이블에 컬럼 복원
    2. user_details에서 데이터 복원
    3. user_details 테이블 삭제
    4. users 테이블에서 tendency_type 컬럼 삭제
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = [col["name"] for col in inspector.get_columns("users")]

    # 1. users 테이블에 컬럼 복원
    if "username" not in user_columns:
        op.add_column("users", sa.Column("username", sa.String(50), nullable=True))
    if "email" not in user_columns:
        op.add_column("users", sa.Column("email", sa.String(100), nullable=True))
    if "fcm_token" not in user_columns:
        op.add_column("users", sa.Column("fcm_token", sa.String(500), nullable=True))
    if "terms_accepted" not in user_columns:
        op.add_column(
            "users", sa.Column("terms_accepted", sa.Boolean(), default=False, nullable=False)
        )

    # 2. user_details에서 데이터 복원
    existing_tables = inspector.get_table_names()
    if "user_details" in existing_tables:
        op.execute(
            """
            UPDATE users u
            SET username = ud.username,
                email = ud.email,
                fcm_token = ud.fcm_token,
                terms_accepted = ud.terms_accepted
            FROM user_details ud
            WHERE u.id = ud.user_id
            """
        )

    # 3. user_details 테이블 삭제
    if "user_details" in existing_tables:
        op.drop_table("user_details")

    # 4. users 테이블에서 tendency_type 컬럼 삭제
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "tendency_type" in user_columns:
        op.drop_column("users", "tendency_type")
