"""Auth Feature Containers"""

from dependency_injector import containers, providers


# ===================
# Service Containers
# ===================
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


# ===================
# UseCase Containers
# ===================
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


# ===================
# Aggregate Container
# ===================
class AuthContainer(containers.DeclarativeContainer):
    """인증 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.user_container import UserContainer

    core: CoreContainer = providers.DependenciesContainer()
    user: UserContainer = providers.DependenciesContainer()

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
        user_repo=user.user_repo,
        user_use_case=user.user_use_case,
        auth_service=auth_service,
        kakao_service=kakao_oauth_service,
        google_service=google_oauth_service,
        apple_service=apple_oauth_service,
        naver_service=naver_oauth_service,
    )
