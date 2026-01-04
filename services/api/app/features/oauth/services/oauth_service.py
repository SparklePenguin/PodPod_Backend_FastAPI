from app.core.config import settings
from app.core.session import verify_oauth_state
from app.features.auth.schemas import LoginInfoDto
from app.features.auth.services import AuthService
from app.features.oauth.exceptions import (
    OAuthAuthenticationFailedException,
    OAuthProviderNotSupportedException,
    OAuthStateInvalidException,
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
from app.features.oauth.services.naver_oauth_service import NaverOAuthService
from app.features.session.services.session_service import SessionService
from app.features.users.repositories import UserRepository
from app.features.users.services.user_service import UserService
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


class OAuthService:
    """OAuth 통합 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)
        self._user_service = UserService(session)
        self._session_service = SessionService(session)
        self._auth_service = AuthService(session)
        self._kakao_service = KakaoOAuthService(session)
        self._google_service = GoogleOAuthService(session)
        self._apple_service = AppleOAuthService(session)
        self._naver_service = NaverOAuthService(session)

    # - MARK: 구글 토큰 로그인
    async def sign_in_with_google(self, request: GoogleLoginRequest):
        """Google 로그인 처리"""
        # Google ID 토큰 검증 및 사용자 정보 추출
        oauth_user_info = await self._google_service.verify_google_id_token(
            request.id_token
        )

        return await self.handle_oauth_login(
            oauth_provider=OAuthProvider.GOOGLE,
            oauth_provider_id=str(oauth_user_info.id),
            oauth_user_info=oauth_user_info,
            fcm_token=request.fcm_token,
        )

    # - MARK: 애플 토큰 로그인
    async def sign_in_with_apple(self, request: AppleLoginRequest) -> LoginInfoDto:
        """Apple 로그인 처리"""
        try:
            oauth_user_info = await self._apple_service.get_apple_user_info(request)
        except HTTPException:
            raise
        except ValueError as e:
            raise OAuthTokenInvalidException(provider="apple") from e

        return await self.handle_oauth_login(
            oauth_provider=OAuthProvider.APPLE,
            oauth_provider_id=str(oauth_user_info.id),
            oauth_user_info=oauth_user_info,
            fcm_token=request.fcm_token,
        )

    # - MARK: 카카오 토큰 로그인
    async def sign_in_with_kakao(self, request: KakaoLoginRequest) -> LoginInfoDto:
        """카카오 로그인 처리"""
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

        return await self.handle_oauth_login(
            oauth_provider=OAuthProvider.KAKAO,
            oauth_provider_id=str(oauth_user_info.id),
            oauth_user_info=oauth_user_info,
            fcm_token=request.fcm_token,
        )

    # - MARK: OAuth 콜백 처리
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
        # Apple 케이스 처리
        if provider == OAuthProvider.APPLE:
            # user 파라미터를 dict로 변환 (JSON 문자열인 경우)
            user_dict = None
            if user:
                try:
                    import json

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
                    identity_token=id_token, authorization_code=code, user=user_dict
                )
            )

            # Android Deep Link로 리다이렉트
            return RedirectResponse(
                url=f"intent://callback?{sign_in_response.model_dump(by_alias=True)}"
                "#Intent;package=sparkle_penguin.podpod;"
                f"scheme={settings.APPLE_SCHEME};end"
            )

        # 1. State 검증 (Naver만)
        if provider == OAuthProvider.NAVER:
            if not state:
                raise OAuthAuthenticationFailedException(
                    provider="naver", reason="State 파라미터가 누락되었습니다."
                )
            if not redis:
                raise OAuthAuthenticationFailedException(
                    provider="naver", reason="Redis 연결이 필요합니다."
                )

            is_valid = await verify_oauth_state(state, redis)
            if not is_valid:
                raise OAuthStateInvalidException()

        # 2. 에러 처리
        if error:
            raise OAuthAuthenticationFailedException(
                provider=provider.value,
                reason=f"인가 코드 요청 실패: {error} - {error_description}",
            )

        # 3. 인가 코드 확인
        if not code:
            raise OAuthAuthenticationFailedException(
                provider=provider.value, reason="인가 코드 값 누락"
            )

        # 4. 토큰 요청
        if provider == OAuthProvider.KAKAO:
            token_response = await self._kakao_service.get_kakao_token(code=code)
            oauth_user_info = await self._kakao_service.get_kakao_user_info(
                token_response.access_token
            )
        elif provider == OAuthProvider.NAVER:
            # naver_service는 구현 필요
            # token_response = await self.naver_service.get_naver_token(
            #     code=code, state=state
            # )
            # oauth_user_info = await self.naver_service.get_naver_user_info(
            #     token_response.access_token
            # )
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Naver OAuth는 아직 구현되지 않았습니다.",
            )
        elif provider == OAuthProvider.GOOGLE:
            token_response = await self._google_service.get_google_token(code=code)
            oauth_user_info = await self._google_service.get_google_user_info(
                token_response.access_token
            )
        else:
            raise OAuthProviderNotSupportedException(provider=provider.value)

        # 5. OAuth 로그인 처리
        return await self.handle_oauth_login(
            oauth_provider=provider.value,
            oauth_provider_id=str(oauth_user_info.id),
            oauth_user_info=oauth_user_info,
        )

    # - MARK: 통합 OAuth 로그인
    async def handle_oauth_login(
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
                await self._user_service.restore_user(user, oauth_user_info)

            # FCM 토큰 업데이트
            if fcm_token:
                await self._user_service.update_fcm_token(user.id, fcm_token)

            # commit 후 트랜잭션이 닫힐 수 있으므로 새로운 쿼리로 조회
            # LoginInfoDto는 UserDetailDto를 요구하므로 get_user_with_follow_stats 사용
            # user_id를 사용하여 새로 조회 (세션 상태와 무관하게 동작)
            user_dto = await self._user_service.get_user_with_follow_stats(user_id, user_id)
        else:
            # 2. 새 사용자 생성 (UserDto 반환)
            # create_user 내부에서 이미 commit/refresh 수행
            user_dto = await self._user_service.create_user(
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

    # - MARK: OAuth 인증 URL 생성
    async def get_auth_url(
        self, provider: OAuthProvider, redis: Redis | None = None
    ) -> str:
        """OAuth 인증 URL 생성"""
        if provider == OAuthProvider.KAKAO:
            return self._kakao_service.get_auth_url()
        elif provider == OAuthProvider.GOOGLE:
            return self._google_service.get_auth_url()
        elif provider == OAuthProvider.NAVER:
            if not redis:
                raise OAuthAuthenticationFailedException(
                    provider="naver", reason="Redis 연결이 필요합니다."
                )
            return await self._naver_service.get_auth_url(redis)
        else:
            raise OAuthProviderNotSupportedException(provider=provider.value)
