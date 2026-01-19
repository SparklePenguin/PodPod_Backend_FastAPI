"""카카오 OAuth 서비스"""

import httpx
from fastapi import HTTPException, status

from app.common.schemas.base_response import BaseResponse
from app.core.config import settings
from app.features.oauth.schemas import (
    GetKakaoTokenRequest,
    KakaoTokenResponse,
    OAuthUserInfo,
)


class KakaoOAuthService:
    """카카오 OAuth 서비스 (Stateless)"""

    KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    def __init__(self) -> None:
        """서비스 초기화"""
        self._redirect_uri = settings.KAKAO_REDIRECT_URI
        self._client_id = settings.KAKAO_CLIENT_ID
        self._client_secret = settings.KAKAO_CLIENT_SECRET


    # - MARK: 카카오 액세스 토큰 조회
    async def get_kakao_token(self, code: str) -> KakaoTokenResponse:
        """카카오 인가 코드을 통해 액세스 토큰을 조회"""
        print(f"🔍 DEBUG - code: {code}")

        token_params = GetKakaoTokenRequest(
            client_id=self._client_id,
            redirect_uri=self._redirect_uri,
            code=code,
            client_secret=self._client_secret,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.KAKAO_TOKEN_URL,
                data=token_params.model_dump(exclude_none=True),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
                },
            )

            if response.status_code != 200:
                error_response = BaseResponse.error(
                    http_status=status.HTTP_401_UNAUTHORIZED,
                    error_key="KAKAO_TOKEN_REQUEST_FAILED",
                    error_code=20002,
                    message_ko=f"카카오 액세스 토큰 요청 실패: {response.text}",
                    message_en=f"Kakao access token request failed: {response.text}",
                    dev_note=f"액세스 토큰 요청 실패: {str(response.text)}",
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_response.model_dump(),
                )

            return KakaoTokenResponse(**response.json())

    async def get_kakao_user_info(self, access_token: str) -> OAuthUserInfo:
        """카카오 액세스 토큰으로 사용자 정보 조회"""
        from typing import Any, Dict

        async with httpx.AsyncClient() as client:
            try:
                # property_keys 파라미터로 이메일 정보 요청
                response = await client.get(
                    self.KAKAO_USER_INFO_URL,
                    params={
                        "property_keys": '["kakao_account.email"]'
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
                    },
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Failed to get Kakao user info: {response.text}",
                    )

                user_info: Dict[str, Any] = response.json()
                print(f"🔍 DEBUG - Kakao user info response: {user_info}")

                user_id = str(user_info.get("id", ""))
                kakao_account: Dict[str, Any] = user_info.get("kakao_account", {}) or {}
                profile: Dict[str, Any] = kakao_account.get("profile", {}) or {}

                return OAuthUserInfo(
                    id=user_id,
                    username=profile.get("nickname"),
                    email=kakao_account.get("email"),
                    image_url=profile.get("profile_image_url"),
                )

            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Kakao API request failed: {str(e)}",
                ) from e

    def get_auth_url(self) -> str:
        """카카오 인증 URL 생성"""
        return (
            f"https://kauth.kakao.com/oauth/authorize?"
            f"client_id={self._client_id}&"
            f"redirect_uri={self._redirect_uri}&"
            f"response_type=code&"
            # f"scope=account_email"
        )
