"""의존성 주입 - Container 기반"""

from app.core.container import container
from app.core.database import get_session
from app.deps.redis import get_redis
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


def get_fcm_service():
    """FCM Service 싱글톤 반환"""
    return container.fcm_service()


def get_random_profile_image_service():
    """랜덤 프로필 이미지 서비스 의존성 주입"""
    return container.random_profile_image_service()


def get_oauth_service(session: AsyncSession = Depends(get_session)):
    """OAuth Service 생성"""
    with container.session.override(session):
        return container.oauth_service()


# Artist Use Cases
def get_artist_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Artist UseCase 생성"""
    with container.session.override(session):
        return container.get_artist_use_case()


def get_artists_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Artists UseCase 생성"""
    with container.session.override(session):
        return container.get_artists_use_case()


def get_schedule_by_id_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Schedule By Id UseCase 생성"""
    with container.session.override(session):
        return container.get_schedule_by_id_use_case()


def get_schedules_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Schedules UseCase 생성"""
    with container.session.override(session):
        return container.get_schedules_use_case()


def create_artist_suggestion_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Create Artist Suggestion UseCase 생성"""
    with container.session.override(session):
        return container.create_artist_suggestion_use_case()


def get_suggestion_by_id_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Suggestion By Id UseCase 생성"""
    with container.session.override(session):
        return container.get_suggestion_by_id_use_case()


def get_suggestions_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Suggestions UseCase 생성"""
    with container.session.override(session):
        return container.get_suggestions_use_case()


def get_artist_ranking_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Artist Ranking UseCase 생성"""
    with container.session.override(session):
        return container.get_artist_ranking_use_case()


def get_suggestions_by_artist_name_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Get Suggestions By Artist Name UseCase 생성"""
    with container.session.override(session):
        return container.get_suggestions_by_artist_name_use_case()


def get_user_use_case(
    session: AsyncSession = Depends(get_session),
):
    """User UseCase 생성"""
    with container.session.override(session):
        return container.user_use_case()


def get_user_artist_use_case(
    session: AsyncSession = Depends(get_session),
):
    """User Artist UseCase 생성"""
    with container.session.override(session):
        return container.user_artist_use_case()


def get_block_user_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Block User UseCase 생성"""
    with container.session.override(session):
        return container.block_user_use_case()


def get_user_notification_use_case(
    session: AsyncSession = Depends(get_session),
):
    """User Notification UseCase 생성"""
    with container.session.override(session):
        return container.user_notification_use_case()


def get_tendency_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Tendency UseCase 생성"""
    with container.session.override(session):
        return container.tendency_use_case()


def get_session_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Session UseCase 생성"""
    with container.session.override(session):
        return container.session_use_case()


def get_report_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Report UseCase 생성"""
    with container.session.override(session):
        return container.report_use_case()


def get_location_use_case(
    session: AsyncSession = Depends(get_session),
):
    """Location UseCase 생성"""
    with container.session.override(session):
        return container.location_use_case()


def get_notification_service(
    session: AsyncSession = Depends(get_session),
):
    """Notification Service 생성"""
    with container.session.override(session):
        return container.notification_service()


def get_like_notification_service(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
):
    """Like Notification Service 생성"""
    with container.session.override(session):
        return container.like_notification_service()


def get_review_notification_service(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
):
    """Review Notification Service 생성"""
    with container.session.override(session):
        return container.review_notification_service()


def get_review_service(
    session: AsyncSession = Depends(get_session),
    notification_service=Depends(get_review_notification_service),
):
    """Review Service 생성"""
    with container.session.override(session):
        return container.review_service()


def get_like_service(
    session: AsyncSession = Depends(get_session),
    notification_service=Depends(get_like_notification_service),
):
    """Like Service 생성"""
    with container.session.override(session):
        return container.like_service()


def get_application_notification_service(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
):
    """Application Notification Service 생성"""
    with container.session.override(session):
        return container.application_notification_service()


def get_application_service(
    session: AsyncSession = Depends(get_session),
    notification_service=Depends(get_application_notification_service),
):
    """Application Service 생성"""
    with container.session.override(session):
        return container.application_service()


def get_application_use_case(
    session: AsyncSession = Depends(get_session),
    application_service=Depends(get_application_service),
):
    """Application UseCase 생성"""
    with container.session.override(session):
        return container.application_use_case()


def get_like_use_case(
    session: AsyncSession = Depends(get_session),
    like_service=Depends(get_like_service),
):
    """Like UseCase 생성"""
    with container.session.override(session):
        return container.like_use_case()


def get_review_use_case(
    session: AsyncSession = Depends(get_session),
    review_service=Depends(get_review_service),
):
    """Review UseCase 생성"""
    with container.session.override(session):
        return container.review_use_case()


def get_follow_use_case(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
):
    """Follow UseCase 생성"""
    with container.session.override(session):
        return container.follow_use_case()


def get_pod_service(
    session: AsyncSession = Depends(get_session),
    review_service=Depends(get_review_service),
    like_service=Depends(get_like_service),
    follow_use_case=Depends(get_follow_use_case),
    fcm_service=Depends(get_fcm_service),
    application_service=Depends(get_application_service),
):
    """Pod Service 생성"""
    with container.session.override(session):
        return container.pod_service()


def get_pod_use_case(
    session: AsyncSession = Depends(get_session),
    pod_service=Depends(get_pod_service),
    follow_use_case=Depends(get_follow_use_case),
    fcm_service=Depends(get_fcm_service),
):
    """Pod UseCase 생성"""
    with container.session.override(session):
        return container.pod_use_case()


def get_websocket_service():
    """WebSocket Service 싱글톤 반환"""
    return container.websocket_service()


def get_chat_service(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
    redis: Redis = Depends(get_redis),
):
    """Chat Service 생성 (WebSocket 서비스 + Redis 포함)"""
    with container.session.override(session), container.redis.override(redis):
        return container.chat_service()


def get_chat_use_case(
    session: AsyncSession = Depends(get_session),
    chat_service=Depends(get_chat_service),
    redis: Redis = Depends(get_redis),
):
    """Chat UseCase 생성"""
    with container.session.override(session), container.redis.override(redis):
        return container.chat_use_case()
