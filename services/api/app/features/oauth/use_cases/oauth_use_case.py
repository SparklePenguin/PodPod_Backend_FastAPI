"""OAuth Use Case - OAuth 인증 비즈니스 로직 처리"""

import json
from typing import TYPE_CHECKING

from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.auth.schemas import LoginInfoDto
from app.features.oauth.exceptions import (
    OAuthAuthenticationFailedException,
    OAuthProviderNotSupportedException,
    OAuthTokenInvalidException,
)
from app.features.oauth.schemas import (
    AppleLoginRequest,
    AppleUserInfo,
    GoogleLoginRequest,
    KakaoLoginRequest,
    OAuthProvider,
    OAuthUserInfo,
)
from app.features.oauth.services.apple_oauth_service import AppleOAuthService
from app.features.oauth.services.google_oauth_service import GoogleOAuthService
from app.features.oauth.services.kakao_oauth_service import KakaoOAuthService
from app.features.users.repositories import UserRepository

if TYPE_CHECKING:
    from app.features.auth.services import AuthService
    from app.features.users.use_cases.user_use_case import UserUseCase


class OAuthUseCase:
    """OAuth 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
            self,
            session: AsyncSession,
            user_repo: UserRepository,
            user_use_case: "UserUseCase",
            auth_service: "AuthService",
            kakao_service: KakaoOAuthService,
            google_service: GoogleOAuthService,
            apple_service: AppleOAuthService,
    ) -> None:
        """
        Args:
            session: 데이터베이스 세션
            user_repo: 사용자 레포지토리
            user_use_case: 사용자 유스케이스
            auth_service: 인증 서비스
            kakao_service: 카카오 OAuth 서비스
            google_service: 구글 OAuth 서비스
            apple_service: 애플 OAuth 서비스
        """
        self._session = session
        self._user_repo = user_repo
        self._user_use_case = user_use_case
        self._auth_service = auth_service
        self._kakao_service = kakao_service
        self._google_service = google_service
        self._apple_service = apple_service

        self._ANDROID_PACKAGE_NAME = settings.ANDROID_PACKAGE_NAME

    # MARK: - 구글 로그인
    async def sign_in_with_google(self, request: GoogleLoginRequest) -> LoginInfoDto:
        """Google 로그인 처리"""
        try:
            # Google ID 토큰 검증 및 사용자 정보 추출
            oauth_user_info = await self._google_service.verify_google_id_token(
                request.id_token
            )

            result = await self._handle_oauth_login(
                oauth_provider=OAuthProvider.GOOGLE,
                oauth_provider_id=str(oauth_user_info.id),
                oauth_user_info=oauth_user_info,
                fcm_token=request.fcm_token,
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 애플 로그인
    async def sign_in_with_apple(self, request: AppleLoginRequest) -> LoginInfoDto:
        """Apple 로그인 처리"""
        try:
            try:
                oauth_user_info = await self._apple_service.get_apple_user_info(request)
            except HTTPException:
                raise
            except ValueError as e:
                raise OAuthTokenInvalidException(provider="apple") from e

            result = await self._handle_oauth_login(
                oauth_provider=OAuthProvider.APPLE,
                oauth_provider_id=str(oauth_user_info.id),
                oauth_user_info=oauth_user_info,
                fcm_token=request.fcm_token,
            )
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 카카오 로그인
    async def sign_in_with_kakao(self, request: KakaoLoginRequest) -> LoginInfoDto:
        """카카오 로그인 처리"""
        try:
            try:
                oauth_user_info = await self._kakao_service.get_kakao_user_info(
                    request.access_token
                )
            except HTTPException:
                raise
            except Exception as e:
                raise OAuthAuthenticationFailedException(
                    provider="kakao", reason=str(e)
                ) from e

            result = await self._handle_oauth_login(
                oauth_provider=OAuthProvider.KAKAO,
                oauth_provider_id=str(oauth_user_info.id),
                oauth_user_info=oauth_user_info,
                fcm_token=request.fcm_token,
            )
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
            id_token: str | None = None,
            user: str | None = None,
    ) -> LoginInfoDto | RedirectResponse:
        """통합 OAuth 콜백 처리"""
        try:
            # Apple 케이스 처리
            if provider == OAuthProvider.APPLE:
                return await self._handle_apple_callback(
                    code=code,
                    error=error,
                    error_description=error_description,
                    id_token=id_token,
                    user=user,
                )
            #  에러 처리
            if error:
                raise OAuthAuthenticationFailedException(
                    provider=provider.value,
                    reason=f"인가 코드 요청 실패: {error} - {error_description}",
                )

            # 인가 코드 확인
            if not code:
                raise OAuthAuthenticationFailedException(
                    provider=provider.value, reason="인가 코드 값 누락"
                )

            # 토큰 요청
            oauth_user_info = await self._get_oauth_user_info_by_code(
                provider, code, state
            )

            # OAuth 로그인 처리
            result = await self._handle_oauth_login(
                oauth_provider=provider.value,
                oauth_provider_id=str(oauth_user_info.id),
                oauth_user_info=oauth_user_info,
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
            base_url: str | None = None,
    ) -> str:
        """OAuth 인증 URL 생성"""
        if provider == OAuthProvider.KAKAO:
            return self._kakao_service.get_auth_url()

        elif provider == OAuthProvider.GOOGLE:
            return self._google_service.get_auth_url()

        elif provider == OAuthProvider.APPLE:
            return self._apple_service.get_auth_url(base_url=base_url)
        else:
            raise OAuthProviderNotSupportedException(provider=provider.value)

    # MARK: - Private 메서드
    async def _handle_apple_callback(
            self,
            code: str | None,
            error: str | None,
            error_description: str | None,
            id_token: str | None,
            user: str | None,
    ) -> RedirectResponse:
        """Apple OAuth 콜백 처리"""
        # user 파라미터를 dict로 변환 (JSON 문자열인 경우)
        user_dict: AppleUserInfo | None = None
        if user:
            try:
                user_json = json.loads(user)
                if user_json:
                    user_dict = AppleUserInfo(**user_json)
            except (json.JSONDecodeError, Exception):
                user_dict = None

        # 에러 처리
        if error:
            raise OAuthAuthenticationFailedException(
                provider="apple",
                reason=error_description or "Apple authentication failed",
            )

        # Authorization Code가 없는 경우
        if not code:
            raise OAuthAuthenticationFailedException(
                provider="apple", reason="Authorization code is required"
            )

        # ID Token이 없는 경우
        if not id_token:
            raise OAuthTokenInvalidException(provider="apple")

        # Apple 로그인 처리
        sign_in_response = await self.sign_in_with_apple(
            AppleLoginRequest(
                identityToken=id_token,
                authorizationCode=code,
                user=user_dict
            )
        )

        # Android Deep Link로 리다이렉트
        return RedirectResponse(
            url=f"intent://callback?{sign_in_response.model_dump(by_alias=True)}"
                f"#Intent;package={self._ANDROID_PACKAGE_NAME};"
                f"scheme={settings.APPLE_SCHEME};end"
        )

    async def _get_oauth_user_info_by_code(
            self, provider: OAuthProvider, code: str, state: str | None
    ) -> OAuthUserInfo:
        """인가 코드로 OAuth 사용자 정보 조회"""
        if provider == OAuthProvider.KAKAO:
            token_response = await self._kakao_service.get_kakao_token(code=code)
            return await self._kakao_service.get_kakao_user_info(
                token_response.access_token
            )
        elif provider == OAuthProvider.GOOGLE:
            token_response = await self._google_service.get_google_token(code=code)
            return await self._google_service.get_google_user_info(
                token_response.access_token
            )
        else:
            raise OAuthProviderNotSupportedException(provider=provider.value)

    async def _handle_oauth_login(
            self,
            oauth_provider: str,
            oauth_provider_id: str,
            oauth_user_info: OAuthUserInfo,
            fcm_token: str | None = None,
    ) -> LoginInfoDto:
        """OAuth 로그인 통합 처리"""
        # 1. 기존 사용자 확인
        user = await self._user_repo.get_by_auth_provider_id(
            auth_provider=oauth_provider, auth_provider_id=oauth_provider_id
        )

        if user:
            # User 모델에서 user_id 가져오기 (commit 전에 저장)
            user_id = user.id

            # 소프트 삭제된 경우 복구
            if user.is_del:
                await self._user_use_case.restore_user(user, oauth_user_info)

            # FCM 토큰 업데이트
            if fcm_token:
                await self._user_use_case.update_fcm_token(user.id, fcm_token)

            # commit 후 트랜잭션이 닫힐 수 있으므로 새로운 쿼리로 조회
            # LoginInfoDto는 UserDetailDto를 요구하므로 get_user_with_follow_stats 사용
            # user_id를 사용하여 새로 조회 (세션 상태와 무관하게 동작)
            user_dto = await self._user_use_case.get_user_with_follow_stats(
                user_id, user_id
            )
        else:
            # 2. 새 사용자 생성 (UserDto 반환)
            # create_user 내부에서 이미 commit/refresh 수행
            user_dto = await self._user_use_case.create_user(
                email=oauth_user_info.email,
                name=oauth_user_info.username,
                nickname=oauth_user_info.nickname,
                profile_image=oauth_user_info.image_url,
                auth_provider=oauth_provider,
                auth_provider_id=oauth_user_info.id,
                fcm_token=fcm_token,
            )
            user_id = user_dto.id

        # 3. JWT 토큰 생성
        credential = await self._auth_service.create_credential(user_id)

        return LoginInfoDto(credential=credential, user=user_dto)
