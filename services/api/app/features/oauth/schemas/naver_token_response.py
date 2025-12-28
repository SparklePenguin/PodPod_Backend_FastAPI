from pydantic import BaseModel


class NaverTokenResponse(BaseModel):
    """(내부)네이버 토큰 응답"""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    model_config = {"populate_by_name": True}
