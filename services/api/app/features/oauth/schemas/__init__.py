"""OAuth feature schemas"""

from .apple_login_request import AppleLoginRequest, AppleUserInfo
from .apple_token_response import AppleTokenResponse
from .get_google_token_request import GetGoogleTokenRequest
from .get_kakao_token_request import GetKakaoTokenRequest
from .get_naver_token_request import GetNaverTokenRequest
from .google_login_request import GoogleLoginRequest
from .google_token_response import GoogleTokenResponse
from .kakao_login_request import KakaoLoginRequest
from .kakao_token_response import KakaoTokenResponse
from .naver_token_response import NaverTokenResponse
from .oauth_provider import OAuthProvider
from .oauth_user_info import OAuthUserInfo

__all__ = [
    "AppleLoginRequest",
    "AppleUserInfo",
    "AppleTokenResponse",
    "GetGoogleTokenRequest",
    "GetKakaoTokenRequest",
    "GetNaverTokenRequest",
    "GoogleLoginRequest",
    "GoogleTokenResponse",
    "KakaoLoginRequest",
    "KakaoTokenResponse",
    "NaverTokenResponse",
    "OAuthProvider",
    "OAuthUserInfo",
]
