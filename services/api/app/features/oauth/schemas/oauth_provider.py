from enum import Enum


class OAuthProvider(str, Enum):
    """OAuth 제공자 열거형"""

    KAKAO = "kakao"
    APPLE = "apple"
    GOOGLE = "google"
    NAVER = "naver"
