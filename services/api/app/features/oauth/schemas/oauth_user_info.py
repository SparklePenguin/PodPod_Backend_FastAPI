from pydantic import BaseModel


class OAuthUserInfo(BaseModel):
    """(내부)OAuth 유저 정보"""

    id: str  # OAuth 제공자의 사용자 고유 ID
    username: str | None = None
    nickname: str | None = None
    email: str | None = None
    image_url: str | None = None
