"""의존성 주입 - Container 기반"""

from app.core.container import container
from app.core.database import get_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_fcm_service():
    """FCM Service 싱글톤 반환"""
    return container.fcm_service()


def get_random_profile_image_service():
    """랜덤 프로필 이미지 서비스 의존성 주입"""
    return container.random_profile_image_service()


def get_artist_service(session: AsyncSession = Depends(get_session)):
    """Artist Service 생성"""
    with container.session.override(session):
        return container.artist_service()


def get_artist_schedule_service(
    session: AsyncSession = Depends(get_session),
):
    """Artist Schedule Service 생성"""
    with container.session.override(session):
        return container.artist_schedule_service()


def get_artist_suggestion_service(
    session: AsyncSession = Depends(get_session),
):
    """Artist Suggestion Service 생성"""
    with container.session.override(session):
        return container.artist_suggestion_service()


def get_oauth_service(session: AsyncSession = Depends(get_session)):
    """OAuth Service 생성"""
    with container.session.override(session):
        return container.oauth_service()


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


def get_location_service(
    session: AsyncSession = Depends(get_session),
):
    """Location Service 생성"""
    with container.session.override(session):
        return container.location_service()


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


def get_follow_service(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
):
    """Follow Service 생성"""
    with container.session.override(session):
        return container.follow_service()


def get_pod_service(
    session: AsyncSession = Depends(get_session),
    review_service=Depends(get_review_service),
    like_service=Depends(get_like_service),
    follow_service=Depends(get_follow_service),
    fcm_service=Depends(get_fcm_service),
    application_service=Depends(get_application_service),
):
    """Pod Service 생성"""
    with container.session.override(session):
        return container.pod_service()


def get_pod_use_case(
    session: AsyncSession = Depends(get_session),
    pod_service=Depends(get_pod_service),
    follow_service=Depends(get_follow_service),
    fcm_service=Depends(get_fcm_service),
):
    """Pod UseCase 생성"""
    with container.session.override(session):
        return container.pod_use_case()


def get_chat_service(
    session: AsyncSession = Depends(get_session),
    fcm_service=Depends(get_fcm_service),
):
    """Chat Service 생성 (WebSocket 서비스 포함)"""
    with container.session.override(session):
        return container.chat_service()


def get_chat_use_case(
    session: AsyncSession = Depends(get_session),
    chat_service=Depends(get_chat_service),
):
    """Chat UseCase 생성"""
    with container.session.override(session):
        return container.chat_use_case()
