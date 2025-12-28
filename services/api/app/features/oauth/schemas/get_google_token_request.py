from pydantic import BaseModel


class GetGoogleTokenRequest(BaseModel):
    """(내부)구글 토큰 요청"""

    grant_type: str = "authorization_code"
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str
