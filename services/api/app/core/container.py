"""의존성 주입 컨테이너"""

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.services.fcm_service import FCMService

# Repositories
from app.features.artists.repositories.artist_repository import ArtistRepository
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.pods.repositories.application_repository import (
    ApplicationRepository,
)
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.session.repositories.session_repository import SessionRepository
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.users.repositories import (
    BlockUserRepository,
    UserNotificationRepository,
    UserReportRepository,
    UserRepository,
)
from app.features.users.repositories.user_artist_repository import (
    UserArtistRepository,
)

# Services
from app.features.artists.services.artist_schedule_service import (
    ArtistScheduleService,
)
from app.features.artists.services.artist_service import ArtistService
from app.features.artists.services.artist_suggestion_service import (
    ArtistSuggestionService,
)
from app.features.chat.services.chat_service import ChatService
from app.features.follow.services.follow_service import FollowService
from app.features.locations.services.location_service import LocationService
from app.features.notifications.services.notification_dto_service import (
    NotificationDtoService,
)
from app.features.notifications.services.notification_service import (
    NotificationService,
)
from app.features.oauth.services.oauth_service import OAuthService
from app.features.pods.services.application_notification_service import (
    ApplicationNotificationService,
)
from app.features.pods.services.application_service import ApplicationService
from app.features.pods.services.like_notification_service import (
    LikeNotificationService,
)
from app.features.pods.services.like_service import LikeService
from app.features.pods.services.pod_notification_service import (
    PodNotificationService,
)
from app.features.pods.services.pod_service import PodService
from app.features.pods.services.review_notification_service import (
    ReviewNotificationService,
)
from app.features.pods.services.review_service import ReviewService
from app.features.tendencies.services.tendency_calculation_service import (
    TendencyCalculationService,
)
from app.features.users.services.random_profile_image_service import (
    RandomProfileImageService,
)
from app.features.users.services.user_dto_service import UserDtoService
from app.features.users.services.user_state_service import UserStateService

# Use Cases
from app.features.chat.use_cases.chat_use_case import ChatUseCase
from app.features.pods.use_cases.application_use_case import ApplicationUseCase
from app.features.pods.use_cases.like_use_case import LikeUseCase
from app.features.pods.use_cases.pod_use_case import PodUseCase
from app.features.pods.use_cases.review_use_case import ReviewUseCase
from app.features.reports.use_cases.report_use_case import ReportUseCase
from app.features.session.use_cases.session_use_case import SessionUseCase
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase
from app.features.users.use_cases.block_user_use_case import BlockUserUseCase
from app.features.users.use_cases.user_artist_use_case import UserArtistUseCase
from app.features.users.use_cases.user_notification_use_case import (
    UserNotificationUseCase,
)
from app.features.users.use_cases.user_use_case import UserUseCase


class Container(containers.DeclarativeContainer):
    """애플리케이션 의존성 컨테이너"""

    # Configuration
    config = providers.Configuration()

    # Core Services (Singleton)
    fcm_service = providers.Singleton(FCMService)
    random_profile_image_service = providers.Singleton(RandomProfileImageService)

    # DTO & Calculation Services (Singleton - stateless)
    user_dto_service = providers.Singleton(UserDtoService)
    user_state_service = providers.Singleton(UserStateService)
    notification_dto_service = providers.Singleton(NotificationDtoService)
    tendency_calculation_service = providers.Singleton(TendencyCalculationService)

    # Repositories (Factory - session dependent)
    user_repository = providers.Factory(UserRepository, session=providers.Dependency())
    user_artist_repository = providers.Factory(
        UserArtistRepository, session=providers.Dependency()
    )
    block_user_repository = providers.Factory(
        BlockUserRepository, session=providers.Dependency()
    )
    user_notification_repository = providers.Factory(
        UserNotificationRepository, session=providers.Dependency()
    )
    user_report_repository = providers.Factory(
        UserReportRepository, session=providers.Dependency()
    )

    artist_repository = providers.Factory(
        ArtistRepository, session=providers.Dependency()
    )

    follow_repository = providers.Factory(
        FollowRepository, session=providers.Dependency()
    )

    pod_repository = providers.Factory(PodRepository, session=providers.Dependency())
    application_repository = providers.Factory(
        ApplicationRepository, session=providers.Dependency()
    )
    pod_like_repository = providers.Factory(
        PodLikeRepository, session=providers.Dependency()
    )
    pod_review_repository = providers.Factory(
        PodReviewRepository, session=providers.Dependency()
    )

    notification_repository = providers.Factory(
        NotificationRepository, session=providers.Dependency()
    )

    tendency_repository = providers.Factory(
        TendencyRepository, session=providers.Dependency()
    )

    session_repository = providers.Factory(
        SessionRepository, session=providers.Dependency()
    )

    chat_room_repository = providers.Factory(
        ChatRoomRepository, session=providers.Dependency()
    )

    # Services (Factory - session or other dependencies)
    artist_service = providers.Factory(ArtistService, session=providers.Dependency())
    artist_schedule_service = providers.Factory(
        ArtistScheduleService, session=providers.Dependency()
    )
    artist_suggestion_service = providers.Factory(
        ArtistSuggestionService, session=providers.Dependency()
    )

    oauth_service = providers.Factory(OAuthService, session=providers.Dependency())

    location_service = providers.Factory(
        LocationService, session=providers.Dependency()
    )

    notification_service = providers.Factory(
        NotificationService, session=providers.Dependency()
    )

    follow_service = providers.Factory(
        FollowService,
        session=providers.Dependency(),
        fcm_service=fcm_service,
    )

    # Notification Services
    # Note: Repository providers need session, so we create them inline
    like_notification_service = providers.Factory(
        LikeNotificationService,
        session=providers.Dependency(),
        fcm_service=fcm_service,
        user_repo=providers.Factory(
            UserRepository, session=providers.Dependency()
        ),
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        like_repo=providers.Factory(
            PodLikeRepository, session=providers.Dependency()
        ),
    )

    review_notification_service = providers.Factory(
        ReviewNotificationService,
        session=providers.Dependency(),
        fcm_service=fcm_service,
        user_repo=providers.Factory(
            UserRepository, session=providers.Dependency()
        ),
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
    )

    application_notification_service = providers.Factory(
        ApplicationNotificationService,
        session=providers.Dependency(),
        fcm_service=fcm_service,
        user_repo=providers.Factory(
            UserRepository, session=providers.Dependency()
        ),
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        like_repo=providers.Factory(
            PodLikeRepository, session=providers.Dependency()
        ),
    )

    pod_notification_service = providers.Factory(
        PodNotificationService,
        session=providers.Dependency(),
        fcm_service=fcm_service,
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
    )

    # Pod Services
    like_service = providers.Factory(
        LikeService,
        session=providers.Dependency(),
        like_repo=providers.Factory(
            PodLikeRepository, session=providers.Dependency()
        ),
        notification_service=like_notification_service,
    )

    review_service = providers.Factory(
        ReviewService,
        session=providers.Dependency(),
        review_repo=providers.Factory(
            PodReviewRepository, session=providers.Dependency()
        ),
        user_repo=providers.Factory(
            UserRepository, session=providers.Dependency()
        ),
        notification_service=review_notification_service,
    )

    application_service = providers.Factory(
        ApplicationService,
        session=providers.Dependency(),
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        application_repo=providers.Factory(
            ApplicationRepository, session=providers.Dependency()
        ),
        user_repo=providers.Factory(
            UserRepository, session=providers.Dependency()
        ),
        notification_service=application_notification_service,
    )

    pod_service = providers.Factory(
        PodService,
        session=providers.Dependency(),
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        application_repo=providers.Factory(
            ApplicationRepository, session=providers.Dependency()
        ),
        review_repo=providers.Factory(
            PodReviewRepository, session=providers.Dependency()
        ),
        like_repo=providers.Factory(
            PodLikeRepository, session=providers.Dependency()
        ),
        user_repo=providers.Factory(
            UserRepository, session=providers.Dependency()
        ),
        application_service=application_service,
        user_use_case=user_use_case,  # Use the defined user_use_case provider
        notification_service=pod_notification_service,
        review_service=review_service,
        like_service=like_service,
        follow_service=follow_service,
    )

    # Chat Service
    chat_service = providers.Factory(
        ChatService,
        session=providers.Dependency(),
        websocket_service=providers.Callable(
            lambda: __import__(
                "app.features.chat.services.websocket_service", fromlist=["WebSocketService"]
            ).WebSocketService()
            if settings.USE_WEBSOCKET_CHAT
            else None
        ),
        fcm_service=fcm_service,
    )

    # Use Cases
    user_use_case = providers.Factory(
        UserUseCase,
        session=providers.Dependency(),
        user_repo=user_repository,
        user_artist_repo=user_artist_repository,
        follow_service=follow_service,
        follow_repo=follow_repository,
        pod_application_repo=application_repository,
        pod_repo=pod_repository,
        pod_like_repo=pod_like_repository,
        notification_repo=notification_repository,
        user_notification_repo=user_notification_repository,
        tendency_repo=tendency_repository,
        user_state_service=user_state_service,
        user_dto_service=user_dto_service,
    )

    user_artist_use_case = providers.Factory(
        UserArtistUseCase,
        session=providers.Dependency(),
        user_artist_repo=user_artist_repository,
        artist_repo=artist_repository,
    )

    block_user_use_case = providers.Factory(
        BlockUserUseCase,
        session=providers.Dependency(),
        block_repo=block_user_repository,
        user_repo=user_repository,
        follow_repo=follow_repository,
        tendency_repo=tendency_repository,
    )

    user_notification_use_case = providers.Factory(
        UserNotificationUseCase,
        session=providers.Dependency(),
        notification_repo=user_notification_repository,
        notification_dto_service=notification_dto_service,
    )

    tendency_use_case = providers.Factory(
        TendencyUseCase,
        session=providers.Dependency(),
        tendency_repo=tendency_repository,
        calculation_service=tendency_calculation_service,
    )

    session_use_case = providers.Factory(
        SessionUseCase,
        session=providers.Dependency(),
        session_repo=session_repository,
    )

    report_use_case = providers.Factory(
        ReportUseCase,
        session=providers.Dependency(),
        report_repo=user_report_repository,
        user_repo=user_repository,
        block_repo=block_user_repository,
        follow_repo=follow_repository,
    )

    application_use_case = providers.Factory(
        ApplicationUseCase,
        session=providers.Dependency(),
        application_service=application_service,
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        application_repo=providers.Factory(
            ApplicationRepository, session=providers.Dependency()
        ),
    )

    like_use_case = providers.Factory(
        LikeUseCase,
        session=providers.Dependency(),
        like_service=like_service,
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        like_repo=providers.Factory(
            PodLikeRepository, session=providers.Dependency()
        ),
    )

    review_use_case = providers.Factory(
        ReviewUseCase,
        session=providers.Dependency(),
        review_service=review_service,
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        review_repo=providers.Factory(
            PodReviewRepository, session=providers.Dependency()
        ),
    )

    pod_use_case = providers.Factory(
        PodUseCase,
        session=providers.Dependency(),
        pod_service=pod_service,
        pod_repo=providers.Factory(PodRepository, session=providers.Dependency()),
        notification_service=pod_notification_service,
        follow_service=follow_service,
    )

    chat_use_case = providers.Factory(
        ChatUseCase,
        session=providers.Dependency(),
        chat_service=chat_service,
        chat_room_repo=chat_room_repository,
    )


# 전역 컨테이너 인스턴스
container = Container()
