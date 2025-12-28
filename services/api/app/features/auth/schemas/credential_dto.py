from pydantic import BaseModel, Field


class CredentialDto(BaseModel):
    """토큰 정보 응답 DTO"""

    access_token: str = Field(..., serialization_alias="accessToken")
    refresh_token: str = Field(..., serialization_alias="refreshToken")

    model_config = {"populate_by_name": True}
