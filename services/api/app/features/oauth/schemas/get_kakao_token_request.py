from pydantic import BaseModel


class GetKakaoTokenRequest(BaseModel):
    """(내부)카카오 토큰 요청"""

    grant_type: str = "authorization_code"  # authorization_code로 고정
    client_id: str  # REST API 키 (앱 키)
    redirect_uri: str  # 인가 코드가 리다이렉트된 URI
    code: str  # 인가 코드 요청으로 얻은 인가 코드
    client_secret: str | None = None  # 토큰 발급 시 보안 강화용 코드
