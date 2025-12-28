from pydantic import BaseModel


class GetNaverTokenRequest(BaseModel):
    """(내부)네이버 토큰 요청"""

    grant_type: str = "authorization_code"
    client_id: str
    client_secret: str
    code: str
    state: str | None = None
