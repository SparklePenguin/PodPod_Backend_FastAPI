"""Application Container - 모든 Feature Container 조립

레벨 구조:
- Level 1: Core만 의존 (Tendency, Artist, Session, Location, Follow)
- Level 2: Core + Level1 의존 (Notification, Pod, Chat)
- Level 3: 여러 Feature 의존 (User)
- Level 4: User 의존 (Auth, Report) - user 관련 provider를 직접 주입받음

설계 원칙:
- 중첩 컨테이너 대신 필요한 의존만 직접 주입
- FeatureContainer는 외부에서 사용할 provider만 노출
- 레벨 의존성이 코드에 명시적으로 표현됨
"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.features.artists.repositories.artist_repository import ArtistRepository
from app.features.artists.use_cases.artist_schedule_use_cases import (
    GetScheduleByIdUseCase,
    GetSchedulesUseCase,
)
from app.features.artists.use_cases.artist_suggestion_use_cases import (
    CreateArtistSuggestionUseCase,
    GetArtistRankingUseCase,
    GetSuggestionByIdUseCase,
    GetSuggestionsByArtistNameUseCase,
    GetSuggestionsUseCase,
)
from app.features.artists.use_cases.artist_use_cases import (
    GetArtistsUseCase,
    GetArtistUseCase,
)
from app.features.auth.services import AuthService
from app.features.chat.repositories.chat_repository import ChatRepository
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.chat.services.chat_message_service import ChatMessageService
from app.features.chat.services.chat_notification_service import ChatNotificationService
from app.features.chat.services.chat_pod_service import ChatPodService
from app.features.chat.use_cases.chat_room_use_case import ChatRoomUseCase
from app.features.chat.use_cases.chat_use_case import ChatUseCase
from app.features.follow.repositories.follow_list_repository import FollowListRepository
from app.features.follow.repositories.follow_notification_repository import (
    FollowNotificationRepository,
)
from app.features.follow.repositories.follow_pod_repository import FollowPodRepository
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.follow.repositories.follow_stats_repository import FollowStatsRepository
from app.features.follow.services.follow_notification_service import (
    FollowNotificationService,
)
from app.features.follow.use_cases.follow_use_case import FollowUseCase
from app.features.locations.repositories.location_repository import LocationRepository
from app.features.locations.use_cases.location_use_case import LocationUseCase
from app.features.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.notifications.services.notification_dto_service import (
    NotificationDtoService,
)
from app.features.notifications.use_cases.notification_use_case import (
    NotificationUseCase,
)
from app.features.oauth.services.apple_oauth_service import AppleOAuthService
from app.features.oauth.services.google_oauth_service import GoogleOAuthService
from app.features.oauth.services.kakao_oauth_service import KakaoOAuthService
from app.features.oauth.services.naver_oauth_service import NaverOAuthService
from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase
from app.features.pods.repositories.application_repository import ApplicationRepository
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.services.application_dto_service import ApplicationDtoService
from app.features.pods.services.application_notification_service import (
    ApplicationNotificationService,
)
from app.features.pods.services.like_notification_service import LikeNotificationService
from app.features.pods.services.pod_enrichment_service import PodEnrichmentService
from app.features.pods.services.pod_notification_service import PodNotificationService
from app.features.pods.services.review_dto_service import ReviewDtoService
from app.features.pods.services.review_notification_service import (
    ReviewNotificationService,
)
from app.features.pods.use_cases.application_use_case import ApplicationUseCase
from app.features.pods.use_cases.like_use_case import LikeUseCase
from app.features.pods.use_cases.pod_query_use_case import PodQueryUseCase
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
    UserNotificationRepository,
    UserReportRepository,
    UserRepository,
)
from app.features.users.repositories.user_artist_repository import UserArtistRepository
from app.features.users.services.user_dto_service import UserDtoService
from app.features.users.services.user_state_service import UserStateService
from app.features.users.use_cases.block_user_use_case import BlockUserUseCase
from app.features.users.use_cases.user_artist_use_case import UserArtistUseCase
from app.features.users.use_cases.user_notification_use_case import (
    UserNotificationUseCase,
)
from app.features.users.use_cases.user_use_case import UserUseCase


# MARK: - Level 1: Core만 의존
class TendencyFeatureContainer(containers.DeclarativeContainer):
    """성향 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    tendency_repo = providers.Factory(TendencyRepository, session=core.session)
    calculation_service = providers.Factory(TendencyCalculationService)
    tendency_use_case = providers.Factory(
        TendencyUseCase,
        session=core.session,
        tendency_repo=tendency_repo,
        calculation_service=calculation_service,
    )


class ArtistFeatureContainer(containers.DeclarativeContainer):
    """아티스트 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    artist_repo = providers.Factory(ArtistRepository, session=core.session)

    # UseCase들
    get_artist_use_case = providers.Factory(GetArtistUseCase, session=core.session)
    get_artists_use_case = providers.Factory(GetArtistsUseCase, session=core.session)
    get_schedule_by_id_use_case = providers.Factory(
        GetScheduleByIdUseCase, session=core.session
    )
    get_schedules_use_case = providers.Factory(GetSchedulesUseCase, session=core.session)
    create_artist_suggestion_use_case = providers.Factory(
        CreateArtistSuggestionUseCase, session=core.session
    )
    get_suggestion_by_id_use_case = providers.Factory(
        GetSuggestionByIdUseCase, session=core.session
    )
    get_suggestions_use_case = providers.Factory(
        GetSuggestionsUseCase, session=core.session
    )
    get_artist_ranking_use_case = providers.Factory(
        GetArtistRankingUseCase, session=core.session
    )
    get_suggestions_by_artist_name_use_case = providers.Factory(
        GetSuggestionsByArtistNameUseCase, session=core.session
    )


class SessionFeatureContainer(containers.DeclarativeContainer):
    """세션 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    session_repo = providers.Factory(SessionRepository, session=core.session)
    session_use_case = providers.Factory(
        SessionUseCase,
        session=core.session,
        session_repo=session_repo,
    )


class LocationFeatureContainer(containers.DeclarativeContainer):
    """위치 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    location_repo = providers.Factory(LocationRepository, session=core.session)
    location_use_case = providers.Factory(
        LocationUseCase,
        session=core.session,
        location_repo=location_repo,
    )


class FollowFeatureContainer(containers.DeclarativeContainer):
    """팔로우 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    follow_repo = providers.Factory(FollowRepository, session=core.session)
    follow_list_repo = providers.Factory(FollowListRepository, session=core.session)
    follow_stats_repo = providers.Factory(FollowStatsRepository, session=core.session)
    follow_notification_repo = providers.Factory(
        FollowNotificationRepository, session=core.session
    )
    follow_pod_repo = providers.Factory(FollowPodRepository, session=core.session)
    pod_repo = providers.Factory(PodRepository, session=core.session)
    like_repo = providers.Factory(PodLikeRepository, session=core.session)
    review_repo = providers.Factory(PodReviewRepository, session=core.session)
    user_repo = providers.Factory(UserRepository, session=core.session)

    # Services
    follow_notification_service = providers.Factory(
        FollowNotificationService,
        session=core.session,
        follow_noti_repo=follow_notification_repo,
        follow_repo=follow_repo,
        follow_list_repo=follow_list_repo,
        pod_repo=pod_repo,
        user_repo=user_repo,
        fcm_service=core.fcm_service,
    )

    # UseCase
    follow_use_case = providers.Factory(
        FollowUseCase,
        session=core.session,
        follow_repo=follow_repo,
        follow_list_repo=follow_list_repo,
        follow_stats_repo=follow_stats_repo,
        follow_notification_repo=follow_notification_repo,
        follow_pod_repo=follow_pod_repo,
        pod_repo=pod_repo,
        like_repo=like_repo,
        review_repo=review_repo,
        user_repo=user_repo,
        follow_notification_service=follow_notification_service,
    )


# MARK: - Level 2: Core + Level1 의존
class NotificationFeatureContainer(containers.DeclarativeContainer):
    """알림 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()
    tendency_repo = providers.Dependency()  # Level 1에서 주입 (개별 provider)

    notification_repo = providers.Factory(NotificationRepository, session=core.session)
    notification_dto_service = providers.Factory(
        NotificationDtoService, tendency_repo=tendency_repo
    )
    notification_use_case = providers.Factory(
        NotificationUseCase,
        session=core.session,
        notification_repo=notification_repo,
        tendency_repo=tendency_repo,
        dto_service=notification_dto_service,
    )


class PodFeatureContainer(containers.DeclarativeContainer):
    """파티 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()
    follow_use_case = providers.Dependency()  # Level 1에서 주입 (개별 provider)

    # Repositories
    pod_repo = providers.Factory(PodRepository, session=core.session)
    application_repo = providers.Factory(ApplicationRepository, session=core.session)
    pod_like_repo = providers.Factory(PodLikeRepository, session=core.session)
    pod_review_repo = providers.Factory(PodReviewRepository, session=core.session)
    user_repo = providers.Factory(UserRepository, session=core.session)

    # Services
    review_dto_service = providers.Factory(
        ReviewDtoService, session=core.session, user_repo=user_repo
    )
    application_dto_service = providers.Factory(
        ApplicationDtoService, session=core.session, user_repo=user_repo
    )
    like_notification_service = providers.Factory(
        LikeNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        user_repo=user_repo,
        pod_repo=pod_repo,
        like_repo=pod_like_repo,
    )
    review_notification_service = providers.Factory(
        ReviewNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        user_repo=user_repo,
        pod_repo=pod_repo,
    )
    application_notification_service = providers.Factory(
        ApplicationNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        user_repo=user_repo,
        pod_repo=pod_repo,
        like_repo=pod_like_repo,
    )
    pod_notification_service = providers.Factory(
        PodNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        pod_repo=pod_repo,
    )
    pod_enrichment_service = providers.Factory(
        PodEnrichmentService,
        pod_repo=pod_repo,
        application_repo=application_repo,
        review_repo=pod_review_repo,
        like_repo=pod_like_repo,
        user_repo=user_repo,
        application_dto_service=application_dto_service,
        review_dto_service=review_dto_service,
    )

    # UseCases
    application_use_case = providers.Factory(
        ApplicationUseCase,
        session=core.session,
        pod_repo=pod_repo,
        application_repo=application_repo,
        user_repo=user_repo,
        notification_service=application_notification_service,
    )
    like_use_case = providers.Factory(
        LikeUseCase,
        session=core.session,
        like_repo=pod_like_repo,
        pod_repo=pod_repo,
        notification_service=like_notification_service,
    )
    review_use_case = providers.Factory(
        ReviewUseCase,
        session=core.session,
        review_repo=pod_review_repo,
        pod_repo=pod_repo,
        user_repo=user_repo,
        notification_service=review_notification_service,
    )
    pod_query_use_case = providers.Factory(
        PodQueryUseCase,
        session=core.session,
        pod_repo=pod_repo,
        user_repo=user_repo,
        enrichment_service=pod_enrichment_service,
        follow_use_case=follow_use_case,
    )
    pod_use_case = providers.Factory(
        PodUseCase,
        session=core.session,
        pod_repo=pod_repo,
        enrichment_service=pod_enrichment_service,
        notification_service=pod_notification_service,
        follow_use_case=follow_use_case,
    )


class ChatFeatureContainer(containers.DeclarativeContainer):
    """채팅 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    # Repositories
    chat_repo = providers.Factory(
        ChatRepository, session=core.session, redis=core.redis
    )
    chat_room_repo = providers.Factory(ChatRoomRepository, session=core.session)
    user_repo = providers.Factory(UserRepository, session=core.session)
    pod_repo = providers.Factory(PodRepository, session=core.session)

    # Services
    message_service = providers.Factory(
        ChatMessageService,
        chat_repo=chat_repo,
        user_repo=user_repo,
        redis=core.redis,
    )
    pod_service = providers.Factory(ChatPodService, pod_repo=pod_repo)
    notification_service = providers.Factory(
        ChatNotificationService,
        session=core.session,
        user_repo=user_repo,
        chat_room_repo=chat_room_repo,
        fcm_service=core.fcm_service,
        redis=core.redis,
    )

    # UseCases
    chat_use_case = providers.Factory(
        ChatUseCase,
        session=core.session,
        user_repo=user_repo,
        chat_room_repo=chat_room_repo,
        message_service=message_service,
        pod_service=pod_service,
        notification_service=notification_service,
        websocket_service=core.websocket_service,
    )
    chat_room_use_case = providers.Factory(
        ChatRoomUseCase,
        session=core.session,
        chat_room_repo=chat_room_repo,
        chat_repo=chat_repo,
        redis=core.redis,
    )


# MARK: - Level 3: 여러 Feature 의존
class UserFeatureContainer(containers.DeclarativeContainer):
    """사용자 Feature 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()
    follow_repo = providers.Dependency()  # Level 1에서 주입 (개별 provider)
    follow_use_case = providers.Dependency()  # Level 1에서 주입 (개별 provider)
    notification_repo = providers.Dependency()  # Level 2에서 주입 (개별 provider)
    tendency_repo = providers.Dependency()  # Level 1에서 주입 (개별 provider)
    notification_dto_service = providers.Dependency()  # Level 2에서 주입 (개별 provider)

    # Repositories
    user_repo = providers.Factory(UserRepository, session=core.session)
    user_artist_repo = providers.Factory(UserArtistRepository, session=core.session)
    block_user_repo = providers.Factory(BlockUserRepository, session=core.session)
    user_notification_repo = providers.Factory(
        UserNotificationRepository, session=core.session
    )
    user_report_repo = providers.Factory(UserReportRepository, session=core.session)
    artist_repo = providers.Factory(ArtistRepository, session=core.session)
    pod_repo = providers.Factory(PodRepository, session=core.session)
    application_repo = providers.Factory(ApplicationRepository, session=core.session)
    pod_like_repo = providers.Factory(PodLikeRepository, session=core.session)

    # Services
    user_dto_service = providers.Singleton(UserDtoService)
    user_state_service = providers.Singleton(UserStateService)

    # UseCases
    user_use_case = providers.Factory(
        UserUseCase,
        session=core.session,
        user_repo=user_repo,
        user_artist_repo=user_artist_repo,
        follow_use_case=follow_use_case,
        follow_repo=follow_repo,
        pod_application_repo=application_repo,
        pod_repo=pod_repo,
        pod_like_repo=pod_like_repo,
        notification_repo=notification_repo,
        user_notification_repo=user_notification_repo,
        tendency_repo=tendency_repo,
        user_state_service=user_state_service,
        user_dto_service=user_dto_service,
    )
    block_user_use_case = providers.Factory(
        BlockUserUseCase,
        session=core.session,
        block_repo=block_user_repo,
        user_repo=user_repo,
        follow_repo=follow_repo,
        tendency_repo=tendency_repo,
    )
    user_notification_use_case = providers.Factory(
        UserNotificationUseCase,
        session=core.session,
        notification_repo=user_notification_repo,
        notification_dto_service=notification_dto_service,
    )
    user_artist_use_case = providers.Factory(
        UserArtistUseCase,
        session=core.session,
        user_artist_repo=user_artist_repo,
        artist_repo=artist_repo,
    )


# MARK: - Level 4: User 의존 (직접 주입!)
class AuthFeatureContainer(containers.DeclarativeContainer):
    """인증 Feature 컨테이너 - user 관련 provider를 직접 주입받음"""

    core: CoreContainer = providers.DependenciesContainer()
    user_repo = providers.Dependency()  # UserFeature에서 주입 (개별 provider)
    user_use_case = providers.Dependency()  # UserFeature에서 주입 (개별 provider)

    # Services
    auth_service = providers.Factory(AuthService, session=core.session)
    kakao_oauth_service = providers.Singleton(KakaoOAuthService)
    google_oauth_service = providers.Singleton(GoogleOAuthService)
    apple_oauth_service = providers.Singleton(AppleOAuthService)
    naver_oauth_service = providers.Singleton(NaverOAuthService)

    # UseCase
    oauth_use_case = providers.Factory(
        OAuthUseCase,
        session=core.session,
        user_repo=user_repo,
        user_use_case=user_use_case,
        auth_service=auth_service,
        kakao_service=kakao_oauth_service,
        google_service=google_oauth_service,
        apple_service=apple_oauth_service,
        naver_service=naver_oauth_service,
    )


class ReportFeatureContainer(containers.DeclarativeContainer):
    """신고 Feature 컨테이너 - user 관련 provider를 직접 주입받음"""

    core: CoreContainer = providers.DependenciesContainer()
    user_repo = providers.Dependency()  # UserFeature에서 주입 (개별 provider)
    follow_repo = providers.Dependency()  # FollowFeature에서 주입 (개별 provider)

    # Repositories
    user_report_repo = providers.Factory(UserReportRepository, session=core.session)
    block_user_repo = providers.Factory(BlockUserRepository, session=core.session)

    # UseCase
    report_use_case = providers.Factory(
        ReportUseCase,
        session=core.session,
        report_repo=user_report_repo,
        user_repo=user_repo,
        block_repo=block_user_repo,
        follow_repo=follow_repo,
    )


# MARK: - Aggregate Container
class ApplicationContainer(containers.DeclarativeContainer):
    """애플리케이션 최상위 컨테이너

    레벨별로 의존성을 명시적으로 주입:
    - Level 1: core만 주입
    - Level 2: core + Level 1 provider 주입
    - Level 3: core + Level 1,2 provider 주입
    - Level 4: core + 필요한 provider 직접 주입
    """

    # Core Infrastructure
    core: CoreContainer = providers.Container(CoreContainer)

    # Level 1: Core만 의존
    tendency_feature: TendencyFeatureContainer = providers.Container(
        TendencyFeatureContainer, core=core
    )
    artist_feature: ArtistFeatureContainer = providers.Container(
        ArtistFeatureContainer, core=core
    )
    session_feature: SessionFeatureContainer = providers.Container(
        SessionFeatureContainer, core=core
    )
    location_feature: LocationFeatureContainer = providers.Container(
        LocationFeatureContainer, core=core
    )
    follow_feature: FollowFeatureContainer = providers.Container(
        FollowFeatureContainer, core=core
    )

    # Level 2: Core + Level 1 의존
    notification_feature: NotificationFeatureContainer = providers.Container(
        NotificationFeatureContainer,
        core=core,
        tendency_repo=tendency_feature.tendency_repo,
    )
    pod_feature: PodFeatureContainer = providers.Container(
        PodFeatureContainer,
        core=core,
        follow_use_case=follow_feature.follow_use_case,
    )
    chat_feature: ChatFeatureContainer = providers.Container(
        ChatFeatureContainer, core=core
    )

    # Level 3: 여러 Feature 의존
    user_feature: UserFeatureContainer = providers.Container(
        UserFeatureContainer,
        core=core,
        follow_repo=follow_feature.follow_repo,
        follow_use_case=follow_feature.follow_use_case,
        notification_repo=notification_feature.notification_repo,
        tendency_repo=tendency_feature.tendency_repo,
        notification_dto_service=notification_feature.notification_dto_service,
    )

    # Level 4: User 의존 (필요한 provider 직접 주입)
    auth_feature: AuthFeatureContainer = providers.Container(
        AuthFeatureContainer,
        core=core,
        user_repo=user_feature.user_repo,
        user_use_case=user_feature.user_use_case,
    )
    report_feature: ReportFeatureContainer = providers.Container(
        ReportFeatureContainer,
        core=core,
        user_repo=user_feature.user_repo,
        follow_repo=follow_feature.follow_repo,
    )


# 전역 컨테이너 인스턴스
container = ApplicationContainer()
