"""OAuth Use Case - OAuth 인증 비즈니스 로직 처리"""

from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import LoginInfoDto
from app.features.oauth.schemas import (
    AppleLoginRequest,
    GoogleLoginRequest,
    KakaoLoginRequest,
    OAuthProvider,
)
from app.features.oauth.services.oauth_service import OAuthService


class OAuthUseCase:
    """OAuth 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        oauth_service: OAuthService,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            oauth_service: OAuth 서비스
        """
        self._session = session
        self._oauth_service = oauth_service

    # MARK: - 구글 로그인
    async def sign_in_with_google(
        self, request: GoogleLoginRequest
    ) -> LoginInfoDto:
        """Google 로그인 처리"""
        try:
            result = await self._oauth_service.sign_in_with_google(request)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 애플 로그인
    async def sign_in_with_apple(self, request: AppleLoginRequest) -> LoginInfoDto:
        """Apple 로그인 처리"""
        try:
            result = await self._oauth_service.sign_in_with_apple(request)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 카카오 로그인
    async def sign_in_with_kakao(self, request: KakaoLoginRequest) -> LoginInfoDto:
        """카카오 로그인 처리"""
        try:
            result = await self._oauth_service.sign_in_with_kakao(request)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - OAuth 콜백 처리
    async def handle_oauth_callback(
        self,
        provider: OAuthProvider,
        code: str | None,
        state: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
        redis: Redis | None = None,
        id_token: str | None = None,
        user: str | None = None,
    ) -> LoginInfoDto | RedirectResponse:
        """통합 OAuth 콜백 처리"""
        try:
            result = await self._oauth_service.handle_oauth_callback(
                provider=provider,
                code=code,
                state=state,
                error=error,
                error_description=error_description,
                redis=redis,
                id_token=id_token,
                user=user,
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - OAuth 인증 URL 생성
    async def get_auth_url(
        self,
        provider: OAuthProvider,
        redis: Redis | None = None,
        base_url: str | None = None,
    ) -> str:
        """OAuth 인증 URL 생성"""
        return await self._oauth_service.get_auth_url(
            provider=provider,
            redis=redis,
            base_url=base_url,
        )
