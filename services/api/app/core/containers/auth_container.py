"""Auth Feature Containers

인증 관련 컨테이너들.
실제 조립은 AuthFeatureContainer(application_container.py)에서 수행됨.
"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.core.containers.user_container import (
    UserRepoContainer,
    UserUseCaseContainer,
)
from app.features.auth.services import AuthService
from app.features.oauth.services.apple_oauth_service import AppleOAuthService
from app.features.oauth.services.google_oauth_service import GoogleOAuthService
from app.features.oauth.services.kakao_oauth_service import KakaoOAuthService
from app.features.oauth.services.naver_oauth_service import NaverOAuthService
from app.features.oauth.use_cases.oauth_use_case import OAuthUseCase


# MARK: - Service Containers
class AuthServiceContainer(containers.DeclarativeContainer):
    """인증 Service 컨테이너"""

    core: CoreContainer = providers.DependenciesContainer()

    auth_service = providers.Factory(AuthService, session=core.session)


class KakaoOAuthServiceContainer(containers.DeclarativeContainer):
    """카카오 OAuth Service 컨테이너"""

    kakao_oauth_service = providers.Singleton(KakaoOAuthService)


class GoogleOAuthServiceContainer(containers.DeclarativeContainer):
    """구글 OAuth Service 컨테이너"""

    google_oauth_service = providers.Singleton(GoogleOAuthService)


class AppleOAuthServiceContainer(containers.DeclarativeContainer):
    """애플 OAuth Service 컨테이너"""

    apple_oauth_service = providers.Singleton(AppleOAuthService)


class NaverOAuthServiceContainer(containers.DeclarativeContainer):
    """네이버 OAuth Service 컨테이너"""

    naver_oauth_service = providers.Singleton(NaverOAuthService)


# MARK: - UseCase Containers
class OAuthUseCaseContainer(containers.DeclarativeContainer):
    """OAuth UseCase 컨테이너
    
    의존성:
    - core: DB 세션
    - user_repo: 사용자 조회
    - user_use_case: 사용자 생성/업데이트
    - auth_service: JWT 토큰 생성
    - *_service: OAuth 제공자별 서비스
    """

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
