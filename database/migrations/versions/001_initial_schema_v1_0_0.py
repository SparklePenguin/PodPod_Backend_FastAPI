"""Initial schema v1.0.0

Revision ID: 001
Revises:
Create Date: 2025-12-09 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    초기 스키마 생성

    주의: 이 마이그레이션은 실제로 테이블을 생성하지 않습니다.
    테이블은 FastAPI 앱 시작 시 Base.metadata.create_all()로 자동 생성됩니다.
    이 마이그레이션은 버전 관리를 위한 기준점(baseline)으로만 사용됩니다.
    """
    # 테이블이 이미 존재한다고 가정하고, 아무 작업도 수행하지 않음
    pass


def downgrade() -> None:
    """
    다운그레이드 시 모든 테이블 삭제

    주의: 이 작업은 모든 데이터를 삭제합니다!
    """
    # 외래 키 제약조건 때문에 역순으로 삭제
    tables_to_drop = [
        'user_tendency_results',
        'tendency_results',
        'tendency_surveys',
        'schedule_members',
        'schedule_contents',
        'preferred_artists',
        'pod_views',
        'pod_reviews',
        'pod_ratings',
        'pod_members',
        'pod_likes',
        'pod_images',
        'pod_applications',
        'pods',
        'notifications',
        'locations',
        'follows',
        'user_reports',
        'user_notification_settings',
        'user_blocks',
        'users',
        'artist_suggestions',
        'artist_schedules',
        'artist_names',
        'artist_images',
        'artist_units',
        'artists',
    ]

    for table in tables_to_drop:
        try:
            op.drop_table(table)
        except Exception:
            # 테이블이 존재하지 않으면 무시
            pass
