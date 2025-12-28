import time
from typing import Optional

import httpx
import requests
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.oauth.services.oauth_service import OauthService


# - MARK: Apple 사용자 정보
class _AppleUserInfo(BaseModel):
    email: Optional[str] = Field(serialization_alias="email")
    firstName: Optional[str] = Field(serialization_alias="firstName")
    lastName: Optional[str] = Field(serialization_alias="lastName")


# - MARK: Apple 로그인 요청
class AppleLoginRequest(BaseModel):
    identity_token: str = Field(serialization_alias="identityToken")
    authorization_code: Optional[str] = Field(
        default=None, serialization_alias="authorizationCode"
    )
    user: Optional[_AppleUserInfo] = Field(default=None, serialization_alias="user")
    fcm_token: Optional[str] = Field(
        default=None,
        serialization_alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = {"populate_by_name": True}


# - MARK: Apple 콜백 파라미터
class AppleCallbackParam(BaseModel):
    code: Optional[str] = None  # Authorization Code
    state: Optional[str] = None  # 요청 시 전달한 state 값
    error: Optional[str] = None  # 에러 코드
    error_description: Optional[str] = None  # 에러 설명
    id_token: Optional[str] = None  # ID Token (일부 경우)
    user: Optional[_AppleUserInfo] = Field(
        default=None,
        serialization_alias="user",
    )  # 사용자 정보 (첫 로그인 시)

    model_config = {
        "populate_by_name": True,
    }


# - MARK: Apple 토큰 응답
class AppleTokenResponse(BaseModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: str = Field(serialization_alias="tokenType", default="Bearer")
    expires_in: int = Field(serialization_alias="expiresIn")
    refresh_token: str = Field(serialization_alias="refreshToken")
    id_token: str = Field(serialization_alias="idToken")

    model_config = {
        "populate_by_name": True,
    }


# - MARK: Apple OAuth 서비스
class AppleOauthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_service = OauthService(db)

    # - MARK: Apple 공개키 목록 가져오기
    async def _get_apple_public_keys(self):
        """Apple의 공개키 목록 가져오기"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.APPLE_PUBLIC_KEYS_URL)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ValueError(f"Failed to fetch Apple public keys: {str(e)}")

    # - MARK: Apple ID 토큰 검증
    async def _verify_apple_token(self, identity_token: str, audience: str) -> dict:
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
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

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
            try:
                payload = jwt.decode(
                    identity_token,
                    public_key_pem,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=settings.APPLE_ISSUER,
                )
            except JWTClaimsError as e:
                if "Invalid audience" in str(e):
                    # Audience 검증 실패 시 디버깅 정보 추가
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Apple token audience mismatch. Expected: {audience}"
                    )

                    # 토큰에서 audience 추출 시도
                    try:
                        unverified_payload = jwt.get_unverified_claims(identity_token)
                        actual_audience = unverified_payload.get("aud")
                        logger.warning(f"Actual audience in token: {actual_audience}")
                    except:
                        pass

                    raise ValueError(
                        "Invalid Apple token audience. Please check APPLE_CLIENT_ID configuration."
                    )
                else:
                    raise e

            return payload

        except JWTError as e:
            raise ValueError(f"Invalid Apple token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")

    # - MARK: Authorization Code를 Access Token과 Refresh Token으로 교환
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

            response = requests.post(
                settings.APPLE_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
            return AppleTokenResponse(**response.json())

        except Exception as e:
            raise ValueError(f"Authorization code exchange failed: {str(e)}")

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
            raise ValueError(f"Failed to create Apple client secret: {str(e)}")

    async def sign_in_with_apple(
        self,
        apple_login_request: AppleLoginRequest,
        audience: str = "com.sparkle-penguin.podpod",
    ):
        """Apple 로그인 처리"""
        try:
            # Apple 토큰 검증
            apple_user_info = await self._verify_apple_token(
                apple_login_request.identity_token,
                audience,
            )

            # Authorization Code가 있으면 토큰 교환
            # 지금은 Apple API를 사용하지 않기 때문에 사용하지 않음
            _apple_tokens = None
            if apple_login_request.authorization_code:
                _apple_tokens = await self._exchange_authorization_code(
                    apple_login_request.authorization_code,
                    audience,
                )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Apple 사용자 정보를 OAuth 서비스 형식에 맞게 변환
        if (
            apple_login_request.user
            and apple_login_request.user.firstName
            and apple_login_request.user.lastName
        ):
            apple_user_info["username"] = (
                apple_login_request.user.firstName + apple_login_request.user.lastName
            )

        return await self.oauth_service.sign_in_with_oauth(
            oauth_provider="apple",
            oauth_user_id=str(apple_user_info["sub"]),
            oauth_user_info=apple_user_info,
            fcm_token=apple_login_request.fcm_token,
        )

    async def handle_apple_callback(
        self, params: AppleCallbackParam
    ) -> RedirectResponse:
        """Apple 콜백 처리 (안드로이드 웹뷰 콜백)"""
        # 에러 처리
        if params.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=params.error_description or "Apple authentication failed",
            )

        # Authorization Code가 없는 경우
        if not params.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required",
            )

        # ID Token이 없는 경우
        if not params.id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token is required",
            )

        # Apple 로그인 처리
        apple_client_id = settings.APPLE_CLIENT_ID
        if not apple_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Apple 클라이언트 ID가 설정되지 않았습니다",
            )
        
        sign_in_response = await self.sign_in_with_apple(
            AppleLoginRequest(
                identity_token=params.id_token,
                authorization_code=params.code,
                user=params.user,
            ),
            audience=apple_client_id,
        )

        # Android Deep Link로 리다이렉트
        return RedirectResponse(
            url=f"intent://callback?{sign_in_response.model_dump(by_alias=True)}"
            "#Intent;package=sparkle_penguin.podpod;"
            f"scheme={settings.APPLE_SCHEME};end"
        )
