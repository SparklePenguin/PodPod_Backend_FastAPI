"""OAuth feature schemas"""

from .oauth_schemas import (
    AppleLoginRequest,
    AppleTokenResponse,
    AppleUserInfo,
    GetGoogleTokenRequest,
    GetKakaoTokenRequest,
    GetNaverTokenRequest,
    GoogleLoginRequest,
    GoogleTokenResponse,
    KakaoLoginRequest,
    KakaoTokenResponse,
    NaverTokenResponse,
    OAuthProvider,
    OAuthUserInfo,
)

__all__ = [
    # OAuth Common
    "OAuthProvider",
    "OAuthUserInfo",
    # Kakao OAuth
    "KakaoLoginRequest",
    "GetKakaoTokenRequest",
    "KakaoTokenResponse",
    # Google OAuth
    "GoogleLoginRequest",
    "GetGoogleTokenRequest",
    "GoogleTokenResponse",
    # Apple OAuth
    "AppleLoginRequest",
    "AppleUserInfo",
    "AppleTokenResponse",
    # Naver OAuth
    "GetNaverTokenRequest",
    "NaverTokenResponse",
]
