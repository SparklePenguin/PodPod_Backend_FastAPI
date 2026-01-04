"""아티스트 제안 관련 스키마"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class ArtistSuggestionDto(BaseModel):
    """아티스트 제안 응답 DTO"""

    id: int = Field(..., description="제안 ID")
    artist_name: str = Field(..., alias="artistName", description="아티스트명")
    reason: str | None = Field(None, description="추천 이유")
    email: str | None = Field(None, description="이메일 주소")
    user_id: int | None = Field(None, alias="userId", description="제안한 사용자 ID")
    created_at: datetime = Field(..., alias="createdAt", description="생성일시")

    class Config:
        from_attributes = True
        populate_by_name = True


class ArtistSuggestionCreateRequest(BaseModel):
    """아티스트 제안 생성 요청"""

    artist_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="아티스트명",
        alias="artistName",
    )
    reason: str | None = Field(None, max_length=1000, description="추천 이유")
    email: EmailStr | None = Field(None, description="이메일 주소")

    @model_validator(mode="before")
    @classmethod
    def validate_email(cls, values):
        """빈 문자열을 None으로 변환"""
        if isinstance(values, dict) and "email" in values:
            if values["email"] == "":
                values["email"] = None
        return values

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "artistName": "아이유",
                "reason": "음악이 정말 좋아요! 많은 사람들이 좋아할 것 같습니다.",
                "email": "user@example.com",
            }
        }


class ArtistSuggestionRankingDto(BaseModel):
    """아티스트 제안 순위 DTO"""

    artist_name: str = Field(..., alias="artistName", description="아티스트명")
    count: int = Field(..., description="요청 횟수")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {"example": {"artist_name": "아이유", "count": 15}}
