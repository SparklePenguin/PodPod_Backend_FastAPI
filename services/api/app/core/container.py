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
from app.features.artists.use_cases.artist_schedule_use_cases import (
    GetScheduleByIdUseCase,
    GetSchedulesUseCase,
)
from app.features.artists.use_cases.artist_suggestion_use_cases import (
    CreateArtistSuggestionUseCase,
    GetArtistRankingUseCase,
    GetSuggestionByIdUseCase,
    GetSuggestionsUseCase,
    GetSuggestionsByArtistNameUseCase,
)
from app.features.artists.use_cases.artist_use_cases import (
    GetArtistUseCase,
    GetArtistsUseCase,
)
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

    # Session Dependency (런타임에 주입됨)
    session = providers.Dependency(instance_of=AsyncSession)

    # Core Services (Singleton)
    fcm_service = providers.Singleton(FCMService)
    random_profile_image_service = providers.Singleton(RandomProfileImageService)

    # DTO & Calculation Services (Singleton - stateless)
    user_dto_service = providers.Singleton(UserDtoService)
    user_state_service = providers.Singleton(UserStateService)
    notification_dto_service = providers.Singleton(NotificationDtoService)
    tendency_calculation_service = providers.Singleton(TendencyCalculationService)

    # Repositories (Factory - session dependent)
    user_repository = providers.Factory(UserRepository, session=session)
    user_artist_repository = providers.Factory(
        UserArtistRepository, session=session
    )
    block_user_repository = providers.Factory(
        BlockUserRepository, session=session
    )
    user_notification_repository = providers.Factory(
        UserNotificationRepository, session=session
    )
    user_report_repository = providers.Factory(
        UserReportRepository, session=session
    )

    artist_repository = providers.Factory(
        ArtistRepository, session=session
    )

    follow_repository = providers.Factory(
        FollowRepository, session=session
    )

    pod_repository = providers.Factory(PodRepository, session=session)
    application_repository = providers.Factory(
        ApplicationRepository, session=session
    )
    pod_like_repository = providers.Factory(
        PodLikeRepository, session=session
    )
    pod_review_repository = providers.Factory(
        PodReviewRepository, session=session
    )

    notification_repository = providers.Factory(
        NotificationRepository, session=session
    )

    tendency_repository = providers.Factory(
        TendencyRepository, session=session
    )

    session_repository = providers.Factory(
        SessionRepository, session=session
    )

    chat_room_repository = providers.Factory(
        ChatRoomRepository, session=session
    )

    # Services (Factory - session or other dependencies)
    oauth_service = providers.Factory(OAuthService, session=session)

    location_service = providers.Factory(
        LocationService, session=session
    )

    notification_service = providers.Factory(
        NotificationService, session=session
    )

    follow_service = providers.Factory(
        FollowService,
        session=session,
        fcm_service=fcm_service,
    )

    # Notification Services
    like_notification_service = providers.Factory(
        LikeNotificationService,
        session=session,
        fcm_service=fcm_service,
        user_repo=user_repository,
        pod_repo=pod_repository,
        like_repo=pod_like_repository,
    )

    review_notification_service = providers.Factory(
        ReviewNotificationService,
        session=session,
        fcm_service=fcm_service,
        user_repo=user_repository,
        pod_repo=pod_repository,
    )

    application_notification_service = providers.Factory(
        ApplicationNotificationService,
        session=session,
        fcm_service=fcm_service,
        user_repo=user_repository,
        pod_repo=pod_repository,
        like_repo=pod_like_repository,
    )

    pod_notification_service = providers.Factory(
        PodNotificationService,
        session=session,
        fcm_service=fcm_service,
        pod_repo=pod_repository,
    )

    # Pod Services
    like_service = providers.Factory(
        LikeService,
        session=session,
        like_repo=pod_like_repository,
        notification_service=like_notification_service,
    )

    review_service = providers.Factory(
        ReviewService,
        session=session,
        review_repo=pod_review_repository,
        user_repo=user_repository,
        notification_service=review_notification_service,
    )

    application_service = providers.Factory(
        ApplicationService,
        session=session,
        pod_repo=pod_repository,
        application_repo=application_repository,
        user_repo=user_repository,
        notification_service=application_notification_service,
    )

    # Use Cases (pod_service보다 먼저 정의 필요)
    user_use_case = providers.Factory(
        UserUseCase,
        session=session,
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

    pod_service = providers.Factory(
        PodService,
        session=session,
        pod_repo=pod_repository,
        application_repo=application_repository,
        review_repo=pod_review_repository,
        like_repo=pod_like_repository,
        user_repo=user_repository,
        application_service=application_service,
        user_use_case=user_use_case,  # Use the defined user_use_case provider
        notification_service=pod_notification_service,
        review_service=review_service,
        like_service=like_service,
        follow_service=follow_service,
        user_dto_service=user_dto_service,
    )

    # Chat Service
    chat_service = providers.Factory(
        ChatService,
        session=session,
        websocket_service=providers.Callable(
            lambda: __import__(
                "app.features.chat.services.websocket_service", fromlist=["WebSocketService"]
            ).WebSocketService()
            if settings.USE_WEBSOCKET_CHAT
            else None
        ),
        fcm_service=fcm_service,
    )

    # Artist Use Cases
    get_artist_use_case = providers.Factory(
        GetArtistUseCase,
        session=session,
    )

    get_artists_use_case = providers.Factory(
        GetArtistsUseCase,
        session=session,
    )

    get_schedule_by_id_use_case = providers.Factory(
        GetScheduleByIdUseCase,
        session=session,
    )

    get_schedules_use_case = providers.Factory(
        GetSchedulesUseCase,
        session=session,
    )

    create_artist_suggestion_use_case = providers.Factory(
        CreateArtistSuggestionUseCase,
        session=session,
    )

    get_suggestion_by_id_use_case = providers.Factory(
        GetSuggestionByIdUseCase,
        session=session,
    )

    get_suggestions_use_case = providers.Factory(
        GetSuggestionsUseCase,
        session=session,
    )

    get_artist_ranking_use_case = providers.Factory(
        GetArtistRankingUseCase,
        session=session,
    )

    get_suggestions_by_artist_name_use_case = providers.Factory(
        GetSuggestionsByArtistNameUseCase,
        session=session,
    )

    user_artist_use_case = providers.Factory(
        UserArtistUseCase,
        session=session,
        user_artist_repo=user_artist_repository,
        artist_repo=artist_repository,
    )

    block_user_use_case = providers.Factory(
        BlockUserUseCase,
        session=session,
        block_repo=block_user_repository,
        user_repo=user_repository,
        follow_repo=follow_repository,
        tendency_repo=tendency_repository,
    )

    user_notification_use_case = providers.Factory(
        UserNotificationUseCase,
        session=session,
        notification_repo=user_notification_repository,
        notification_dto_service=notification_dto_service,
    )

    tendency_use_case = providers.Factory(
        TendencyUseCase,
        session=session,
        tendency_repo=tendency_repository,
        calculation_service=tendency_calculation_service,
    )

    session_use_case = providers.Factory(
        SessionUseCase,
        session=session,
        session_repo=session_repository,
    )

    report_use_case = providers.Factory(
        ReportUseCase,
        session=session,
        report_repo=user_report_repository,
        user_repo=user_repository,
        block_repo=block_user_repository,
        follow_repo=follow_repository,
    )

    application_use_case = providers.Factory(
        ApplicationUseCase,
        session=session,
        application_service=application_service,
        pod_repo=pod_repository,
        application_repo=application_repository,
    )

    like_use_case = providers.Factory(
        LikeUseCase,
        session=session,
        like_service=like_service,
        pod_repo=pod_repository,
        like_repo=pod_like_repository,
    )

    review_use_case = providers.Factory(
        ReviewUseCase,
        session=session,
        review_service=review_service,
        pod_repo=pod_repository,
        review_repo=pod_review_repository,
    )

    pod_use_case = providers.Factory(
        PodUseCase,
        session=session,
        pod_service=pod_service,
        pod_repo=pod_repository,
        notification_service=pod_notification_service,
        follow_service=follow_service,
        user_repo=user_repository,
    )

    chat_use_case = providers.Factory(
        ChatUseCase,
        session=session,
        chat_service=chat_service,
        chat_room_repo=chat_room_repository,
    )


# 전역 컨테이너 인스턴스
container = Container()
