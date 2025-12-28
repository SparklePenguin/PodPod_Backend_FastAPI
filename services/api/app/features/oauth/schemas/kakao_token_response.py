from pydantic import BaseModel, Field


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

    model_config = {"populate_by_name": True}
