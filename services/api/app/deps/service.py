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
from app.features.follow.repositories.follow_repository import FollowRepository
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
from app.features.reports.use_cases.report_use_case import ReportUseCase
from app.features.session.repositories.session_repository import SessionRepository
from app.features.session.use_cases.session_use_case import SessionUseCase
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.tendencies.services.tendency_calculation_service import (
    TendencyCalculationService,
)
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase
from app.features.users.repositories import (
    BlockUserRepository,
    UserReportRepository,
    UserRepository,
)
from app.features.users.repositories.user_artist_repository import (
    UserArtistRepository,
)
from app.features.users.services.random_profile_image_service import (
    RandomProfileImageService,
)
from app.features.users.use_cases.block_user_use_case import BlockUserUseCase
from app.features.users.use_cases.user_artist_use_case import UserArtistUseCase
from app.features.users.use_cases.user_notification_use_case import (
    UserNotificationUseCase,
)
from app.features.users.use_cases.user_use_case import UserUseCase
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_fcm_service() -> FCMService:
    """FCM Service 싱글톤 반환"""
    return FCMService()


def get_random_profile_image_service() -> RandomProfileImageService:
    """랜덤 프로필 이미지 서비스 의존성 주입"""
    return RandomProfileImageService()


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


def get_user_use_case(
    session: AsyncSession = Depends(get_session),
) -> UserUseCase:
    from app.core.services.fcm_service import FCMService
    from app.features.follow.repositories.follow_repository import FollowRepository
    from app.features.follow.services.follow_service import FollowService
    from app.features.pods.repositories.application_repository import (
        ApplicationRepository,
    )
    from app.features.notifications.repositories.notification_repository import (
        NotificationRepository,
    )
    from app.features.pods.repositories.like_repository import PodLikeRepository
    from app.features.pods.repositories.pod_repository import PodRepository
    from app.features.tendencies.repositories.tendency_repository import (
        TendencyRepository,
    )
    from app.features.users.repositories.user_notification_repository import (
        UserNotificationRepository,
    )
    from app.features.users.services.user_dto_service import UserDtoService
    from app.features.users.services.user_state_service import UserStateService

    user_repo = UserRepository(session)
    user_artist_repo = UserArtistRepository(session)
    fcm_service = FCMService()
    follow_service = FollowService(session, fcm_service=fcm_service)
    follow_repo = FollowRepository(session)
    pod_application_repo = ApplicationRepository(session)
    pod_repo = PodRepository(session)
    pod_like_repo = PodLikeRepository(session)
    notification_repo = NotificationRepository(session)
    user_notification_repo = UserNotificationRepository(session)
    tendency_repo = TendencyRepository(session)
    user_state_service = UserStateService()
    user_dto_service = UserDtoService()
    return UserUseCase(
        session=session,
        user_repo=user_repo,
        user_artist_repo=user_artist_repo,
        follow_service=follow_service,
        follow_repo=follow_repo,
        pod_application_repo=pod_application_repo,
        pod_repo=pod_repo,
        pod_like_repo=pod_like_repo,
        notification_repo=notification_repo,
        user_notification_repo=user_notification_repo,
        tendency_repo=tendency_repo,
        user_state_service=user_state_service,
        user_dto_service=user_dto_service,
    )


def get_user_artist_use_case(
    session: AsyncSession = Depends(get_session),
) -> UserArtistUseCase:
    from app.features.artists.repositories.artist_repository import ArtistRepository
    from app.features.users.repositories.user_artist_repository import (
        UserArtistRepository,
    )

    user_artist_repo = UserArtistRepository(session)
    artist_repo = ArtistRepository(session)
    return UserArtistUseCase(
        session=session,
        user_artist_repo=user_artist_repo,
        artist_repo=artist_repo,
    )


def get_block_user_use_case(
    session: AsyncSession = Depends(get_session),
) -> BlockUserUseCase:
    from app.features.follow.repositories.follow_repository import FollowRepository
    from app.features.tendencies.repositories.tendency_repository import (
        TendencyRepository,
    )
    from app.features.users.repositories import BlockUserRepository, UserRepository

    block_repo = BlockUserRepository(session)
    user_repo = UserRepository(session)
    follow_repo = FollowRepository(session)
    tendency_repo = TendencyRepository(session)
    return BlockUserUseCase(
        session=session,
        block_repo=block_repo,
        user_repo=user_repo,
        follow_repo=follow_repo,
        tendency_repo=tendency_repo,
    )


def get_user_notification_use_case(
    session: AsyncSession = Depends(get_session),
) -> UserNotificationUseCase:
    from app.features.notifications.services.notification_dto_service import (
        NotificationDtoService,
    )
    from app.features.users.repositories import UserNotificationRepository

    notification_repo = UserNotificationRepository(session)
    notification_dto_service = NotificationDtoService()
    return UserNotificationUseCase(
        session=session,
        notification_repo=notification_repo,
        notification_dto_service=notification_dto_service,
    )


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


def get_session_use_case(
    session: AsyncSession = Depends(get_session),
) -> SessionUseCase:
    session_repo = SessionRepository(session)
    return SessionUseCase(
        session=session,
        session_repo=session_repo,
    )


def get_report_use_case(
    session: AsyncSession = Depends(get_session),
) -> ReportUseCase:
    report_repo = UserReportRepository(session)
    user_repo = UserRepository(session)
    block_repo = BlockUserRepository(session)
    follow_repo = FollowRepository(session)
    return ReportUseCase(
        session=session,
        report_repo=report_repo,
        user_repo=user_repo,
        block_repo=block_repo,
        follow_repo=follow_repo,
    )


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
    from app.core.services.fcm_service import FCMService
    from app.features.follow.repositories.follow_repository import FollowRepository
    from app.features.follow.services.follow_service import FollowService
    from app.features.pods.repositories.application_repository import (
        ApplicationRepository,
    )
    from app.features.pods.services.pod_notification_service import (
        PodNotificationService,
    )
    from app.features.tendencies.repositories.tendency_repository import (
        TendencyRepository,
    )
    from app.features.users.repositories import UserRepository
    from app.features.users.repositories.user_artist_repository import (
        UserArtistRepository,
    )
    from app.features.users.use_cases.user_use_case import UserUseCase

    pod_repo = PodRepository(session)
    application_repo = ApplicationRepository(session)
    review_repo = PodReviewRepository(session)
    like_repo = PodLikeRepository(session)
    user_repo = UserRepository(session)
    user_artist_repo = UserArtistRepository(session)
    fcm_service = FCMService()
    follow_service = FollowService(session, fcm_service=fcm_service)
    follow_repo = FollowRepository(session)
    pod_application_repo = ApplicationRepository(session)
    tendency_repo = TendencyRepository(session)
    user_use_case = UserUseCase(
        session=session,
        user_repo=user_repo,
        user_artist_repo=user_artist_repo,
        follow_service=follow_service,
        follow_repo=follow_repo,
        pod_application_repo=pod_application_repo,
        tendency_repo=tendency_repo,
    )
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
        user_use_case=user_use_case,
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
