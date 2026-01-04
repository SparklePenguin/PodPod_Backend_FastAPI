from app.core.config import settings
from app.core.database import get_session
from app.core.services.fcm_service import FCMService
from app.features.artists.services.artist_schedule_service import ArtistScheduleService
from app.features.artists.services.artist_service import ArtistService
from app.features.artists.services.artist_suggestion_service import (
    ArtistSuggestionService,
)
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.services.chat_service import ChatService
from app.features.chat.use_cases.chat_use_case import ChatUseCase
from app.features.follow.services.follow_service import FollowService
from app.features.locations.services.location_service import LocationService
from app.features.notifications.services.notification_service import (
    NotificationService,
)
from app.features.oauth.services.oauth_service import OAuthService
from app.features.pods.repositories.application_repository import (
    ApplicationRepository,
)
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.services.application_notification_service import (
    ApplicationNotificationService,
)
from app.features.pods.services.application_service import ApplicationService
from app.features.pods.services.like_notification_service import (
    LikeNotificationService,
)
from app.features.pods.services.like_service import LikeService
from app.features.pods.services.pod_service import PodService
from app.features.pods.services.review_notification_service import (
    ReviewNotificationService,
)
from app.features.pods.services.review_service import ReviewService
from app.features.pods.use_cases.application_use_case import ApplicationUseCase
from app.features.pods.use_cases.like_use_case import LikeUseCase
from app.features.pods.use_cases.pod_use_case import PodUseCase
from app.features.pods.use_cases.review_use_case import ReviewUseCase
from app.features.reports.services.report_service import ReportService
from app.features.session.services.session_service import SessionService
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.tendencies.services.tendency_calculation_service import (
    TendencyCalculationService,
)
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase
from app.features.users.repositories import UserRepository
from app.features.users.services.block_user_service import BlockUserService
from app.features.users.services.user_artist_service import UserArtistService
from app.features.users.services.user_notification_service import (
    UserNotificationService,
)
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


def get_tendency_use_case(
    session: AsyncSession = Depends(get_session),
) -> TendencyUseCase:
    tendency_repo = TendencyRepository(session)
    calculation_service = TendencyCalculationService()
    return TendencyUseCase(
        session=session,
        tendency_repo=tendency_repo,
        calculation_service=calculation_service,
    )


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


def get_like_notification_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> LikeNotificationService:
    user_repo = UserRepository(session)
    pod_repo = PodRepository(session)
    like_repo = PodLikeRepository(session)
    return LikeNotificationService(
        session=session,
        fcm_service=fcm_service,
        user_repo=user_repo,
        pod_repo=pod_repo,
        like_repo=like_repo,
    )


def get_review_notification_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> ReviewNotificationService:
    user_repo = UserRepository(session)
    pod_repo = PodRepository(session)
    return ReviewNotificationService(
        session=session,
        fcm_service=fcm_service,
        user_repo=user_repo,
        pod_repo=pod_repo,
    )


def get_review_service(
    session: AsyncSession = Depends(get_session),
    notification_service: ReviewNotificationService = Depends(
        get_review_notification_service
    ),
) -> ReviewService:
    # session을 직접 사용하기 위해 생성
    review_repo = PodReviewRepository(session)
    user_repo = UserRepository(session)
    return ReviewService(
        session=session,
        review_repo=review_repo,
        user_repo=user_repo,
        notification_service=notification_service,
    )


def get_like_service(
    session: AsyncSession = Depends(get_session),
    notification_service: LikeNotificationService = Depends(
        get_like_notification_service
    ),
) -> LikeService:
    # session을 직접 사용하기 위해 생성
    like_repo = PodLikeRepository(session)
    return LikeService(
        session=session,
        like_repo=like_repo,
        notification_service=notification_service,
    )


def get_application_notification_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> ApplicationNotificationService:
    user_repo = UserRepository(session)
    pod_repo = PodRepository(session)
    like_repo = PodLikeRepository(session)
    return ApplicationNotificationService(
        session=session,
        fcm_service=fcm_service,
        user_repo=user_repo,
        pod_repo=pod_repo,
        like_repo=like_repo,
    )


def get_application_service(
    session: AsyncSession = Depends(get_session),
    notification_service: ApplicationNotificationService = Depends(
        get_application_notification_service
    ),
) -> ApplicationService:
    # session을 직접 사용하기 위해 생성
    pod_repo = PodRepository(session)
    application_repo = ApplicationRepository(session)
    user_repo = UserRepository(session)
    return ApplicationService(
        session=session,
        pod_repo=pod_repo,
        application_repo=application_repo,
        user_repo=user_repo,
        notification_service=notification_service,
    )


def get_application_use_case(
    session: AsyncSession = Depends(get_session),
    application_service: ApplicationService = Depends(get_application_service),
) -> ApplicationUseCase:
    pod_repo = PodRepository(session)
    application_repo = ApplicationRepository(session)
    return ApplicationUseCase(
        session=session,
        application_service=application_service,
        pod_repo=pod_repo,
        application_repo=application_repo,
    )


def get_like_use_case(
    session: AsyncSession = Depends(get_session),
    like_service: LikeService = Depends(get_like_service),
) -> LikeUseCase:
    pod_repo = PodRepository(session)
    like_repo = PodLikeRepository(session)
    return LikeUseCase(
        session=session,
        like_service=like_service,
        pod_repo=pod_repo,
        like_repo=like_repo,
    )


def get_review_use_case(
    session: AsyncSession = Depends(get_session),
    review_service: ReviewService = Depends(get_review_service),
) -> ReviewUseCase:
    pod_repo = PodRepository(session)
    review_repo = PodReviewRepository(session)
    return ReviewUseCase(
        session=session,
        review_service=review_service,
        pod_repo=pod_repo,
        review_repo=review_repo,
    )


def get_follow_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
):
    from app.features.follow.services.follow_service import FollowService

    return FollowService(session, fcm_service=fcm_service)


def get_pod_service(
    session: AsyncSession = Depends(get_session),
    review_service: ReviewService = Depends(get_review_service),
    like_service: LikeService = Depends(get_like_service),
    follow_service: FollowService = Depends(get_follow_service),
    fcm_service: FCMService = Depends(get_fcm_service),
    application_service: ApplicationService = Depends(get_application_service),
) -> PodService:
    from app.features.pods.services.pod_notification_service import (
        PodNotificationService,
    )
    from app.features.users.repositories import UserRepository
    from app.features.users.services.user_service import UserService

    pod_repo = PodRepository(session)
    application_repo = ApplicationRepository(session)
    review_repo = PodReviewRepository(session)
    like_repo = PodLikeRepository(session)
    user_repo = UserRepository(session)
    user_service = UserService(session)
    pod_notification_service = PodNotificationService(
        session=session,
        fcm_service=fcm_service,
        pod_repo=pod_repo,
    )
    return PodService(
        session=session,
        pod_repo=pod_repo,
        application_repo=application_repo,
        review_repo=review_repo,
        like_repo=like_repo,
        user_repo=user_repo,
        application_service=application_service,
        user_service=user_service,
        notification_service=pod_notification_service,
        review_service=review_service,
        like_service=like_service,
        follow_service=follow_service,
    )


def get_pod_use_case(
    session: AsyncSession = Depends(get_session),
    pod_service: PodService = Depends(get_pod_service),
    follow_service: FollowService = Depends(get_follow_service),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> PodUseCase:
    from app.features.pods.services.pod_notification_service import (
        PodNotificationService,
    )

    pod_repo = PodRepository(session)
    pod_notification_service = PodNotificationService(
        session=session,
        fcm_service=fcm_service,
        pod_repo=pod_repo,
    )
    return PodUseCase(
        session=session,
        pod_service=pod_service,
        pod_repo=pod_repo,
        notification_service=pod_notification_service,
        follow_service=follow_service,
    )


def get_chat_service(
    session: AsyncSession = Depends(get_session),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> ChatService:
    """Chat Service 생성 (WebSocket 서비스 포함)"""
    websocket_service = None
    if settings.USE_WEBSOCKET_CHAT:
        from app.features.chat.services.websocket_service import WebSocketService

        websocket_service = WebSocketService()
    return ChatService(
        session=session, websocket_service=websocket_service, fcm_service=fcm_service
    )


def get_chat_use_case(
    session: AsyncSession = Depends(get_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatUseCase:
    """Chat UseCase 생성"""
    chat_room_repo = ChatRoomRepository(session)
    return ChatUseCase(
        session=session,
        chat_service=chat_service,
        chat_room_repo=chat_room_repo,
    )
