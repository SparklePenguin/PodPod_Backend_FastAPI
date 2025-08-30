from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
import requests
from jose import jwt, JWTError
import base64
import json
import time

from app.services.oauth_service import OauthService
from app.schemas.common import SuccessResponse, ErrorResponse
from app.core.config import settings


# - MARK: Apple 사용자 정보
class _AppleUserInfo(BaseModel):
    email: str = Field(alias="email")
    firstName: str = Field(alias="firstName")
    lastName: str = Field(alias="lastName")
    sub: str = Field(alias="sub")


# - MARK: Apple 로그인 요청
class AppleLoginRequest(BaseModel):
    identity_token: str = Field(alias="identityToken")
    authorization_code: Optional[str] = Field(
        default=None,
        alias="authorizationCode",
    )
    user: Optional[_AppleUserInfo] = Field(
        default=None,
        alias="user",
    )

    model_config = {
        "populate_by_name": True,
    }


# - MARK: Apple 토큰 응답
class AppleTokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType", default="Bearer")
    expires_in: int = Field(alias="expiresIn")
    refresh_token: str = Field(alias="refreshToken")
    id_token: str = Field(alias="idToken")

    model_config = {
        "populate_by_name": True,
    }


# - MARK: Apple OAuth 서비스
class AppleOauthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_service = OauthService(db)

    # - MARK: Apple 공개키 목록 가져오기
    def _get_apple_public_keys(self):
        """Apple의 공개키 목록 가져오기"""
        try:
            response = requests.get(self.apple_public_keys_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ValueError(f"Failed to fetch Apple public keys: {str(e)}")

    # - MARK: Apple ID 토큰 검증
    def _verify_apple_token(self, identity_token: str) -> dict:
        """Apple ID 토큰 검증"""
        try:
            # Apple 공개키 가져오기
            public_keys = self._get_apple_public_keys()

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
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
            from cryptography.hazmat.backends import default_backend

            def base64url_decode(data):
                import base64

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
            from cryptography.hazmat.primitives import serialization

            public_key_pem = public_key_obj.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            # 토큰 검증
            payload = jwt.decode(
                identity_token,
                public_key_pem,
                algorithms=["RS256"],
                audience=settings.APPLE_CLIENT_ID,  # Apple App ID
                issuer=settings.APPLE_ISSUER,
            )

            return payload

        except JWTError as e:
            raise ValueError(f"Invalid Apple token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")

    # - MARK: Authorization Code를 Access Token과 Refresh Token으로 교환
    async def _exchange_authorization_code(
        self, authorization_code: str
    ) -> AppleTokenResponse:
        """Authorization Code를 Access Token과 Refresh Token으로 교환"""
        try:
            # Apple Client Secret 생성 (JWT 형식)
            client_secret = self._create_apple_client_secret()

            # 토큰 교환 요청
            token_data = {
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": client_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.APPLE_REDIRECT_URI,
            }

            response = requests.post(
                self.apple_token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")

            return AppleTokenResponse(**response.json())

        except Exception as e:
            raise ValueError(f"Authorization code exchange failed: {str(e)}")

    def _create_apple_client_secret(self) -> str:
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
                "sub": settings.APPLE_CLIENT_ID,  # App ID
            }

            # JWT 생성
            token = jwt.encode(payload, private_key, algorithm="ES256", headers=header)

            return token

        except Exception as e:
            raise ValueError(f"Failed to create Apple client secret: {str(e)}")

    async def sign_in_with_apple(
        self, apple_login_request: AppleLoginRequest
    ) -> SuccessResponse:
        """Apple 로그인 처리"""
        try:
            # Apple 토큰 검증
            apple_user_info = self._verify_apple_token(
                apple_login_request.identity_token
            )

            # Authorization Code가 있으면 토큰 교환
            # 지금은 Apple API를 사용하지 않기 때문에 사용하지 않음
            _apple_tokens = None
            if apple_login_request.authorization_code:
                _apple_tokens = await self._exchange_authorization_code(
                    apple_login_request.authorization_code
                )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="invalid_apple_token",
                    status=400,
                    message=str(e),
                ),
            )

        # Apple 사용자 정보를 OAuth 서비스 형식에 맞게 변환
        apple_user_data = apple_user_info.model_dump()
        apple_user_data["email"] = apple_user_info.get("email")
        apple_user_data["username"] = (
            apple_login_request.user.firstName + apple_login_request.user.lastName
        )

        return self.oauth_service.sign_in_with_oauth(
            oauth_provider="apple",
            oauth_user_id=str(apple_user_info["sub"]),
            oauth_user_info=apple_user_data,
        )
