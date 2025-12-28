"""Naver OAuth service"""

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.base_response import BaseResponse
from app.core.config import settings
from app.features.oauth.schemas.get_naver_token_request import GetNaverTokenRequest
from app.features.oauth.schemas.naver_token_response import NaverTokenResponse
from app.features.oauth.schemas.oauth_user_info import OAuthUserInfo


class NaverOAuthService:
    """네이버 OAuth 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._naver_token_url = "https://nid.naver.com/oauth2.0/token"
        self._naver_user_info_url = "https://openapi.naver.com/v1/nid/me"

    # - MARK: 네이버 액세스 토큰 조회
    async def get_naver_token(
        self, code: str, state: str | None = None
    ) -> NaverTokenResponse:
        """네이버 인가 코드를 통해 액세스 토큰 조회"""

        # 설정에서 네이버 정보 가져오기
        client_id = settings.NAVER_CLIENT_ID
        client_secret = settings.NAVER_CLIENT_SECRET

        print(f"🔍 DEBUG - code: {code}, state: {state}")

        token_params = GetNaverTokenRequest(
            client_id=client_id, client_secret=client_secret, code=code, state=state
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._naver_token_url,
                data=token_params.model_dump(exclude_none=True),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
                },
            )

            if response.status_code != 200:
                error_response = BaseResponse.error(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error_code=20002,
                    message=response.text,
                    dev_note=f"액세스 토큰 요청 실패: {str(response.text)}",
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_response.model_dump(),
                )

            return NaverTokenResponse(**response.json())

    # - MARK: 네이버 사용자 정보 조회
    async def get_naver_user_info(self, access_token: str) -> OAuthUserInfo:
        """네이버 액세스 토큰으로 사용자 정보 조회"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self._naver_user_info_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Failed to get Naver user info: {response.text}",
                    )

                user_info = response.json()
                print(f"🔍 DEBUG - Naver user info response: {user_info}")

                # 네이버는 response.response 안에 실제 데이터가 있음
                naver_response = user_info.get("response", {})
                user_id = naver_response.get("id")

                return OAuthUserInfo(
                    id=str(user_id),
                    username=naver_response.get("name")
                    or naver_response.get("nickname"),
                    email=naver_response.get("email"),
                    image_url=naver_response.get("profile_image"),
                )

            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Naver API request failed: {str(e)}",
                ) from e

    # - MARK: 네이버 인증 URL 생성
    async def get_auth_url(self, redis) -> str:
        """네이버 인증 URL 생성"""
        import secrets

        from app.core.session import save_oauth_state

        # CSRF 방지용 state 값 생성
        state = secrets.token_urlsafe(16)

        # Redis에 state 저장 (10분 유효)
        await save_oauth_state(state, redis, expire_seconds=600)

        # 네이버 인증 URL 생성
        return (
            f"https://nid.naver.com/oauth2.0/authorize?"
            f"response_type=code&"
            f"client_id={settings.NAVER_CLIENT_ID}&"
            f"redirect_uri={settings.NAVER_REDIRECT_URI}&"
            f"state={state}"
        )
