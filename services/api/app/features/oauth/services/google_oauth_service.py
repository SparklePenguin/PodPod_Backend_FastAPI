import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.base_response import BaseResponse
from app.core.config import settings
from app.features.oauth.schemas.get_google_token_request import GetGoogleTokenRequest
from app.features.oauth.schemas.google_token_response import GoogleTokenResponse
from app.features.oauth.schemas.oauth_user_info import OAuthUserInfo


class GoogleOAuthService:
    """구글 OAuth 서비스"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    async def get_google_token(self, code: str) -> GoogleTokenResponse:
        """구글 인가 코드를 통해 액세스 토큰 조회"""

        # 설정에서 구글 정보 가져오기
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET

        print(f"🔍 DEBUG - code: {code}")

        token_params = GetGoogleTokenRequest(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            code=code,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.google_token_url,
                data=token_params.model_dump(exclude_none=True),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
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

            return GoogleTokenResponse(**response.json())

    async def get_google_user_info(self, access_token: str) -> OAuthUserInfo:
        """구글 액세스 토큰으로 사용자 정보 조회"""
        from typing import Any, Dict

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.google_user_info_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Failed to get Google user info: {response.text}",
                    )

                user_info: Dict[str, Any] = response.json()
                print(f"🔍 DEBUG - Google user info response: {user_info}")

                return OAuthUserInfo(
                    id=str(user_info.get("sub", "")),  # Google은 "sub"을 사용
                    username=user_info.get("name"),
                    email=user_info.get("email"),
                    image_url=user_info.get("picture"),
                )

            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Google API request failed: {str(e)}",
                ) from e

    def get_auth_url(self) -> str:
        """구글 인증 URL 생성"""
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "email profile",
            "access_type": "offline",
        }

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
