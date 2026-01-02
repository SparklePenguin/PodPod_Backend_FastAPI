from app.core.config import settings
from app.core.database import get_session
from app.core.services.fcm_service import FCMService
from app.features.artists.services.artist_schedule_service import ArtistScheduleService
from app.features.artists.services.artist_service import ArtistService
from app.features.artists.services.artist_suggestion_service import (
    ArtistSuggestionService,
)
from app.features.chat.services.chat_service import ChatService
from app.features.follow.services.follow_service import FollowService
from app.features.locations.services.location_service import LocationService
from app.features.notifications.services.notification_service import (
    NotificationService,
)
from app.features.oauth.services.oauth_service import OAuthService
from app.features.pods.services.pod_like_service import PodLikeService
from app.features.pods.services.pod_review_service import PodReviewService
from app.features.pods.services.pod_service import PodService
from app.features.pods.services.recruitment_service import RecruitmentService
from app.features.reports.services.report_service import ReportService
from app.features.session.services.session_service import SessionService
from app.features.tendencies.services.tendency_service import TendencyService
from app.features.users.services.block_user_service import BlockUserService
from app.features.users.services.user_notification_service import (
    UserNotificationService,
)
from app.features.users.services.user_artist_service import UserArtistService
from app.features.users.services.user_service import UserService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_fcm_service() -> FCMService:
    """FCM Service 싱글톤 반환"""
    return FCMService()


def get_artist_service(session: AsyncSession = Depends(get_session)) -> ArtistService:
    return ArtistService(session=session)


def get_artist_schedule_service(
    session: AsyncSession = Depends(get_session),
) -> ArtistScheduleService:
    return ArtistScheduleService(session)


def get_artist_suggestion_service(
    session: AsyncSession = Depends(get_session),
) -> ArtistSuggestionService:
    return ArtistSuggestionService(session)


def get_oauth_service(session: AsyncSession = Depends(get_session)) -> OAuthService:
    return OAuthService(session)


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def get_user_artist_service(
    session: AsyncSession = Depends(get_session),
) -> UserArtistService:
    return UserArtistService(session)


def get_block_user_service(
    session: AsyncSession = Depends(get_session),
) -> BlockUserService:
    return BlockUserService(session)


def get_user_notification_service(
    session: AsyncSession = Depends(get_session),
) -> UserNotificationService:
    return UserNotificationService(session)


def get_tendency_service(
    session: AsyncSession = Depends(get_session),
) -> TendencyService:
    return TendencyService(session=session)


def get_session_service(
    session: AsyncSession = Depends(get_session),
) -> SessionService:
    return SessionService(session)


def get_report_service(
    session: AsyncSession = Depends(get_session),
) -> ReportService:
    return ReportService(session)


def get_location_service(
    session: AsyncSession = Depends(get_session),
) -> LocationService:
    return LocationService(session)


def get_notification_service(
    session: AsyncSession = Depends(get_session),
) -> NotificationService:
    return NotificationService(session=session)


def get_pod_review_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> PodReviewService:
    return PodReviewService(session=session, fcm_service=fcm_service)


def get_pod_like_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> PodLikeService:
    return PodLikeService(session, fcm_service=fcm_service)


def get_recruitment_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> RecruitmentService:
    return RecruitmentService(session, fcm_service=fcm_service)


def get_follow_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
):
    from app.features.follow.services.follow_service import FollowService

    return FollowService(session, fcm_service=fcm_service)


def get_pod_service(
    session: AsyncSession = Depends(get_session),
    review_service: PodReviewService = Depends(get_pod_review_service),
    like_service: PodLikeService = Depends(get_pod_like_service),
    recruitment_service: RecruitmentService = Depends(get_recruitment_service),
    follow_service: FollowService = Depends(get_follow_service),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> PodService:
    return PodService(
        session=session,
        review_service=review_service,
        like_service=like_service,
        recruitment_service=recruitment_service,
        follow_service=follow_service,
        fcm_service=fcm_service,
    )


def get_chat_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> ChatService:
    """Chat Service 생성 (WebSocket 서비스 포함)"""
    websocket_service = None
    if settings.USE_WEBSOCKET_CHAT:
        from app.core.services.websocket_service import WebSocketService

        websocket_service = WebSocketService()
    return ChatService(
        session=session, websocket_service=websocket_service, fcm_service=fcm_service
    )
