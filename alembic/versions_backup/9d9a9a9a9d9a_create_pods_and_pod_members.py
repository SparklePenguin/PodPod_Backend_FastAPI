"""create pods and pod_members tables

Revision ID: 9d9a9a9a9d9a
Revises: x43fd96f85b9
Create Date: 2025-09-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d9a9a9a9d9a"
down_revision = "x43fd96f85b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("pods"):
        try:
            op.create_table(
                "pods",
                sa.Column(
                    "id", sa.Integer(), primary_key=True, autoincrement=True, index=True
                ),
                sa.Column(
                    "owner_id",
                    sa.Integer(),
                    sa.ForeignKey("users.id"),
                    nullable=False,
                    index=True,
                ),
                sa.Column("title", sa.String(length=100), nullable=False),
                sa.Column("description", sa.String(length=500), nullable=True),
                sa.Column("image_url", sa.String(length=500), nullable=True),
                sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
                sa.Column("sub_category", sa.Text(), nullable=True),
                sa.Column("capacity", sa.Integer(), nullable=False),
                sa.Column("place", sa.String(length=200), nullable=False),
                sa.Column("address", sa.String(length=300), nullable=False),
                sa.Column("sub_address", sa.String(length=300), nullable=True),
                sa.Column("meeting_date", sa.Date(), nullable=False),
                sa.Column("meeting_time", sa.Time(), nullable=False),
                sa.Column(
                    "is_active",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("1"),
                ),
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                ),
                sa.Column(
                    "updated_at",
                    sa.DateTime(),
                    nullable=True,
                    server_default=sa.text(
                        "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                    ),
                ),
            )
        except Exception:
            pass

    if not insp.has_table("pod_members"):
        try:
            op.create_table(
                "pod_members",
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
                    "role", sa.String(length=20), nullable=False, server_default="owner"
                ),
                sa.Column(
                    "joined_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                ),
                sa.UniqueConstraint(
                    "pod_id", "user_id", name="uq_pod_members_pod_user"
                ),
            )
        except Exception:
            pass


def downgrade() -> None:
    try:
        op.drop_table("pod_members")
    except Exception:
        pass
    try:
        op.drop_table("pods")
    except Exception:
        pass
