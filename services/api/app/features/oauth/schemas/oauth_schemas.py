"""OAuth 인증 관련 스키마"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ============= OAuth Provider =============
class OAuthProvider(str, Enum):
    """OAuth 제공자 열거형"""

    KAKAO = "kakao"
    APPLE = "apple"
    GOOGLE = "google"
    NAVER = "naver"


class OAuthUserInfo(BaseModel):
    """(내부)OAuth 유저 정보"""

    id: str  # OAuth 제공자의 사용자 고유 ID
    username: str | None = None
    nickname: str | None = None
    email: str | None = None
    image_url: str | None = None


# ============= Kakao OAuth =============
class KakaoLoginRequest(BaseModel):
    """카카오 로그인 요청"""

    access_token: str = Field(alias="accessToken")
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = ConfigDict(populate_by_name=True)


class GetKakaoTokenRequest(BaseModel):
    """(내부)카카오 토큰 요청"""

    grant_type: str = "authorization_code"  # authorization_code로 고정
    client_id: str  # REST API 키 (앱 키)
    redirect_uri: str  # 인가 코드가 리다이렉트된 URI
    code: str  # 인가 코드 요청으로 얻은 인가 코드
    client_secret: str | None = None  # 토큰 발급 시 보안 강화용 코드


class KakaoTokenResponse(BaseModel):
    """(내부)카카오 토큰 응답 리스폰"""

    token_type: str = Field(
        default="bearer", alias="token_type"
    )  # 토큰 타입, bearer로 고정
    access_token: str  # 사용자 액세스 토큰 값
    id_token: str | None = Field(default=None)  # ID 토큰 값 (OpenID Connect)
    expires_in: int  # 액세스 토큰과 ID 토큰의 만료 시간(초)
    refresh_token: str  # 사용자 리프레시 토큰 값
    refresh_token_expires_in: int  # 리프레시 토큰 만료 시간(초)
    scope: str | None = Field(
        default=None
    )  # 인증된 사용자의 정보 조회 권한 범위 (공백 구분 문자열)
    fcm_token: str | None = Field(
        default=None, alias="fcmToken", description="FCM 토큰 (푸시 알림용)"
    )

    model_config = ConfigDict(populate_by_name=True)


# ============= Google OAuth =============
class GoogleLoginRequest(BaseModel):
    id_token: str = Field(alias="idToken")
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = ConfigDict(populate_by_name=True)


class GetGoogleTokenRequest(BaseModel):
    """(내부)구글 토큰 요청"""

    grant_type: str = "authorization_code"
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str


class GoogleTokenResponse(BaseModel):
    """(내부)구글 토큰 응답"""

    access_token: str
    refresh_token: str | None = None
    token_type: str
    expires_in: int
    id_token: str | None = None
    scope: str | None = None

    model_config = ConfigDict(populate_by_name=True)


# ============= Apple OAuth =============
class AppleUserInfo(BaseModel):
    email: str | None = Field()
    firstName: str | None = Field(alias="firstName")
    lastName: str | None = Field(alias="lastName")


class AppleLoginRequest(BaseModel):
    identity_token: str = Field(alias="identityToken")
    authorization_code: str | None = Field(default=None, alias="authorizationCode")
    user: AppleUserInfo | None = Field(default=None)
    audience: str | None = Field(
        default=None,
        description="Apple Client ID (Bundle ID for native app, Service ID for web). 생략 시 서버 기본값 사용",
    )
    fcm_token: str | None = Field(
        default=None,
        alias="fcmToken",
        description="FCM 토큰 (푸시 알림용)",
    )

    model_config = ConfigDict(populate_by_name=True)


class AppleTokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(alias="tokenType", default="Bearer")
    expires_in: int = Field(alias="expiresIn")
    refresh_token: str = Field(alias="refreshToken")
    id_token: str = Field(alias="idToken")

    model_config = {
        "populate_by_name": True,
    }


# ============= Naver OAuth =============
class GetNaverTokenRequest(BaseModel):
    """(내부)네이버 토큰 요청"""

    grant_type: str = "authorization_code"
    client_id: str
    client_secret: str
    code: str
    state: str | None = None


class NaverTokenResponse(BaseModel):
    """(내부)네이버 토큰 응답"""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    model_config = ConfigDict(populate_by_name=True)
