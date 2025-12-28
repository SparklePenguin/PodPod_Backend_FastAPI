from pydantic import BaseModel


class GoogleTokenResponse(BaseModel):
    """(내부)구글 토큰 응답"""

    access_token: str
    refresh_token: str | None = None
    token_type: str
    expires_in: int
    id_token: str | None = None
    scope: str | None = None

    model_config = {"populate_by_name": True}
