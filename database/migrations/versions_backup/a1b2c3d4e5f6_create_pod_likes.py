"""create pod_likes

Revision ID: a1b2c3d4e5f6
Revises: 9d9a9a9a9d9a
Create Date: 2025-09-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "9d9a9a9a9d9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("pod_likes"):
        try:
            op.create_table(
                "pod_likes",
                sa.Column(
                    "id", sa.Integer(), primary_key=True, autoincrement=True, index=True
                ),
                sa.Column(
                    "pod_id",
                    sa.Integer(),
                    sa.ForeignKey("pods.id"),
                    nullable=False,
                    index=True,
                ),
                sa.Column(
                    "user_id",
                    sa.Integer(),
                    sa.ForeignKey("users.id"),
                    nullable=False,
                    index=True,
                ),
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                ),
                sa.UniqueConstraint("pod_id", "user_id", name="uq_pod_likes_pod_user"),
            )
        except Exception:
            pass


def downgrade() -> None:
    try:
        op.drop_table("pod_likes")
    except Exception:
        pass
