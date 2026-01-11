"""Auth Feature Containers"""

from dependency_injector import containers, providers


# MARK: - Service Containers
class AuthServiceContainer(containers.DeclarativeContainer):
    """인증 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.auth.services import AuthService

    core: CoreContainer = providers.DependenciesContainer()

    auth_service = providers.Factory(AuthService, session=core.session)


class KakaoOAuthServiceContainer(containers.DeclarativeContainer):
    """카카오 OAuth Service 컨테이너"""

    from app.features.oauth.services.kakao_oauth_service import KakaoOAuthService

    kakao_oauth_service = providers.Singleton(KakaoOAuthService)


class GoogleOAuthServiceContainer(containers.DeclarativeContainer):
    """구글 OAuth Service 컨테이너"""

    from app.features.oauth.services.google_oauth_service import GoogleOAuthService

    google_oauth_service = providers.Singleton(GoogleOAuthService)


class AppleOAuthServiceContainer(containers.DeclarativeContainer):
    """애플 OAuth Service 컨테이너"""

    from app.features.oauth.services.apple_oauth_service import AppleOAuthService

    apple_oauth_service = providers.Singleton(AppleOAuthService)


class NaverOAuthServiceContainer(containers.DeclarativeContainer):
    """네이버 OAuth Service 컨테이너"""

    from app.features.oauth.services.naver_oauth_service import NaverOAuthService

    naver_oauth_service = providers.Singleton(NaverOAuthService)


# MARK: - UseCase Containers
class OAuthUseCaseContainer(containers.DeclarativeContainer):
    """OAuth UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.user_container import (
        UserRepoContainer,
        UserUseCaseContainer,
    )
    from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: UserRepoContainer = providers.DependenciesContainer()
    user_use_case: UserUseCaseContainer = providers.DependenciesContainer()
    auth_service: AuthServiceContainer = providers.DependenciesContainer()
    kakao_service: KakaoOAuthServiceContainer = providers.DependenciesContainer()
    google_service: GoogleOAuthServiceContainer = providers.DependenciesContainer()
    apple_service: AppleOAuthServiceContainer = providers.DependenciesContainer()
    naver_service: NaverOAuthServiceContainer = providers.DependenciesContainer()

    oauth_use_case = providers.Factory(
        OAuthUseCase,
        session=core.session,
        user_repo=user_repo.user_repo,
        user_use_case=user_use_case.user_use_case,
        auth_service=auth_service.auth_service,
        kakao_service=kakao_service.kakao_oauth_service,
        google_service=google_service.google_oauth_service,
        apple_service=apple_service.apple_oauth_service,
        naver_service=naver_service.naver_oauth_service,
    )


# MARK: - Aggregate Container
class AuthContainer(containers.DeclarativeContainer):
    """인증 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import (
        FollowRepoContainer,
        FollowUseCaseContainer,
    )
    from app.core.containers.notification_container import (
        NotificationDtoServiceContainer,
        NotificationRepoContainer,
    )
    from app.core.containers.pod_container import PodRepoContainer
    from app.core.containers.tendency_container import TendencyRepoContainer
    from app.core.containers.user_container import (
        UserArtistRepoContainer,
        UserDtoServiceContainer,
        UserNotificationRepoContainer,
        UserRepoContainer,
        UserStateServiceContainer,
        UserUseCaseContainer,
    )

    core: CoreContainer = providers.DependenciesContainer()

    # User 관련 컨테이너들 직접 생성
    user_repo: UserRepoContainer = providers.Container(UserRepoContainer, core=core)
    user_artist_repo: UserArtistRepoContainer = providers.Container(
        UserArtistRepoContainer, core=core
    )
    user_notification_repo: UserNotificationRepoContainer = providers.Container(
        UserNotificationRepoContainer, core=core
    )
    follow_repo: FollowRepoContainer = providers.Container(FollowRepoContainer, core=core)
    follow_use_case_container: FollowUseCaseContainer = providers.Container(
        FollowUseCaseContainer, core=core
    )
    notification_repo: NotificationRepoContainer = providers.Container(
        NotificationRepoContainer, core=core
    )
    tendency_repo: TendencyRepoContainer = providers.Container(
        TendencyRepoContainer, core=core
    )
    pod_repo: PodRepoContainer = providers.Container(PodRepoContainer, core=core)
    notification_service: NotificationDtoServiceContainer = providers.Container(
        NotificationDtoServiceContainer, tendency_repo=tendency_repo
    )
    user_dto_service: UserDtoServiceContainer = providers.Container(UserDtoServiceContainer)
    user_state_service: UserStateServiceContainer = providers.Container(
        UserStateServiceContainer
    )

    # UserUseCaseContainer 생성
    user_use_case: UserUseCaseContainer = providers.Container(
        UserUseCaseContainer,
        core=core,
        user_repo=user_repo,
        user_artist_repo=user_artist_repo,
        user_notification_repo=user_notification_repo,
        follow_repo=follow_repo,
        follow_use_case=follow_use_case_container,
        notification_repo=notification_repo,
        tendency_repo=tendency_repo,
        pod_repo=pod_repo,
        user_state_service=user_state_service,
        user_dto_service=user_dto_service,
    )

    # Services
    auth_service: AuthServiceContainer = providers.Container(AuthServiceContainer, core=core)
    kakao_oauth_service: KakaoOAuthServiceContainer = providers.Container(
        KakaoOAuthServiceContainer
    )
    google_oauth_service: GoogleOAuthServiceContainer = providers.Container(
        GoogleOAuthServiceContainer
    )
    apple_oauth_service: AppleOAuthServiceContainer = providers.Container(
        AppleOAuthServiceContainer
    )
    naver_oauth_service: NaverOAuthServiceContainer = providers.Container(
        NaverOAuthServiceContainer
    )

    # UseCases
    oauth_use_case: OAuthUseCaseContainer = providers.Container(
        OAuthUseCaseContainer,
        core=core,
        user_repo=user_repo,
        user_use_case=user_use_case,
        auth_service=auth_service,
        kakao_service=kakao_oauth_service,
        google_service=google_oauth_service,
        apple_service=apple_oauth_service,
        naver_service=naver_oauth_service,
    )
