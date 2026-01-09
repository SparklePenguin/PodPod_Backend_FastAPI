"""애플 OAuth 서비스"""

import base64
import logging
import time
from typing import Any, Dict
from urllib.parse import urlencode

import httpx
from app.core.config import settings
from app.features.oauth.schemas import (
    AppleLoginRequest,
    AppleTokenResponse,
    OAuthUserInfo,
)
from fastapi import HTTPException, status
from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError


class AppleOAuthService:
    """애플 OAuth 서비스 (Stateless)"""

    def __init__(self) -> None:
        """서비스 초기화"""
        self._apple_public_keys_url = "https://appleid.apple.com/auth/keys"
        self._apple_token_url = "https://appleid.apple.com/auth/token"
        self._apple_issuer = "https://appleid.apple.com"

    # - MARK: 애플 사용자 정보 조회
    async def get_apple_user_info(self, request: AppleLoginRequest) -> OAuthUserInfo:
        """애플 ID 토큰으로 사용자 정보 조회"""
        # audience가 제공되지 않으면 기본값(APPLE_CLIENT_ID) 사용
        audience = request.audience or settings.APPLE_CLIENT_ID

        try:
            # Apple ID 토큰 검증
            apple_user_info = await self._verify_apple_token(
                request.identity_token, audience
            )

            # Apple 사용자 정보를 OAuth 서비스 형식에 맞게 변환
            username = apple_user_info.get("email", "").split("@")[0]
            if request.user and request.user.firstName and request.user.lastName:
                username = f"{request.user.firstName} {request.user.lastName}"

            return OAuthUserInfo(
                id=str(apple_user_info.get("sub", "")),
                username=username,
                email=apple_user_info.get("email"),
                image_url=None,  # Apple은 프로필 이미지를 제공하지 않음
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Apple token verification failed: {str(e)}",
            ) from e

    # - MARK: Apple 공개키 목록 조회
    async def _get_apple_public_keys(self) -> Dict[str, Any]:
        """Apple의 공개키 목록 가져오기"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._apple_public_keys_url)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch Apple public keys: {str(e)}") from e

    # - MARK: Apple ID 토큰 검증
    async def _verify_apple_token(
        self, identity_token: str, audience: str
    ) -> Dict[str, Any]:
        """Apple ID 토큰 검증"""
        try:
            # Apple 공개키 가져오기
            public_keys = await self._get_apple_public_keys()

            # 토큰 헤더에서 kid (Key ID) 추출
            token_header = jwt.get_unverified_header(identity_token)
            kid = token_header.get("kid")

            if not kid:
                raise ValueError("No Key ID in token header")

            # 해당하는 공개키 찾기
            public_key = None
            for key in public_keys["keys"]:
                if key["kid"] == kid:
                    public_key = key
                    break

            if not public_key:
                raise ValueError("No matching public key found")

            # 공개키를 PEM 형식으로 변환
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

            def base64url_decode(data: str) -> bytes:
                missing_padding = len(data) % 4
                if missing_padding:
                    data += "=" * (4 - missing_padding)
                return base64.urlsafe_b64decode(data)

            numbers = RSAPublicNumbers(
                e=int.from_bytes(base64url_decode(public_key["e"]), "big"),
                n=int.from_bytes(base64url_decode(public_key["n"]), "big"),
            )
            public_key_obj = numbers.public_key(backend=default_backend())

            # PEM 형식으로 변환
            public_key_pem = public_key_obj.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            # 토큰 검증
            try:
                payload = jwt.decode(
                    identity_token,
                    public_key_pem,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=self._apple_issuer,
                )
            except JWTClaimsError as e:
                if "Invalid audience" in str(e):
                    # Audience 검증 실패 시 디버깅 정보 추가
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Apple token audience mismatch. Expected: {audience}"
                    )

                    # 토큰에서 audience 추출 시도
                    try:
                        unverified_payload = jwt.get_unverified_claims(identity_token)
                        actual_audience = unverified_payload.get("aud")
                        logger.warning(f"Actual audience in token: {actual_audience}")
                    except Exception:
                        pass

                    raise ValueError(
                        "Invalid Apple token audience. Please check APPLE_CLIENT_ID configuration."
                    ) from e
                raise ValueError(f"Invalid Apple token claims: {str(e)}") from e

            return payload

        except JWTError as e:
            raise ValueError(f"Invalid Apple token: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}") from e

    # - MARK: Authorization Code 토큰 교환
    async def _exchange_authorization_code(
        self, authorization_code: str, audience: str
    ) -> AppleTokenResponse:
        """Authorization Code를 Access Token과 Refresh Token으로 교환"""
        try:
            # Apple Client Secret 생성 (JWT 형식)
            client_secret = self._create_apple_client_secret(audience)

            # 토큰 교환 요청
            token_data = {
                "client_id": audience,
                "client_secret": client_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.APPLE_REDIRECT_URI,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._apple_token_url,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    raise ValueError(f"Token exchange failed: {response.text}")

                return AppleTokenResponse(**response.json())

        except httpx.RequestError as e:
            raise ValueError(f"Authorization code exchange failed: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Authorization code exchange failed: {str(e)}") from e

    # - MARK: Apple Client Secret 생성
    def _create_apple_client_secret(self, audience: str) -> str:
        """Apple Client Secret 생성 (JWT 형식)"""
        try:
            # Apple Private Key (환경변수에서 가져오기)
            private_key = settings.APPLE_PRIVATE_KEY
            if not private_key:
                raise ValueError("Apple Private Key not configured")

            # JWT 헤더
            header = {
                "alg": "ES256",
                "kid": settings.APPLE_KEY_ID,  # Key ID
            }

            # JWT 페이로드
            payload = {
                "iss": settings.APPLE_TEAM_ID,  # Team ID
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,  # 1시간 만료
                "aud": "https://appleid.apple.com",
                "sub": audience,
            }

            # JWT 생성
            token = jwt.encode(payload, private_key, algorithm="ES256", headers=header)
            return token

        except Exception as e:
            raise ValueError(f"Failed to create Apple client secret: {str(e)}") from e

    # - MARK: Apple 인증 URL 생성
    def get_auth_url(
        self, state: str | None = None, base_url: str | None = None
    ) -> str:
        """Apple 인증 URL 생성"""
        # base_url이 제공되면 동적으로 redirect_uri 생성 (테스트용)
        if base_url:
            redirect_uri = f"{base_url}/api/v1/oauth/apple/callback"
        else:
            redirect_uri = settings.APPLE_REDIRECT_URI

        params = {
            "client_id": settings.APPLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code id_token",
            "response_mode": "form_post",
            "scope": "name email",
        }

        if state:
            params["state"] = state

        return f"https://appleid.apple.com/auth/authorize?{urlencode(params)}"
