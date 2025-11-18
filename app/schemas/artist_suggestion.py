from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from datetime import datetime
from typing import Optional


class ArtistSuggestionCreateRequest(BaseModel):
    """아티스트 제안 생성 요청"""

    artist_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="아티스트명",
        example="아이유",
        alias="artistName",
    )
    reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="추천 이유",
        example="음악이 정말 좋아요!",
        alias="reason",
    )
    email: Optional[EmailStr] = Field(
        None, description="이메일 주소", example="user@example.com", alias="email"
    )

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


class ArtistSuggestionDto(BaseModel):
    """아티스트 제안 응답 DTO"""

    id: int = Field(..., alias="id", description="제안 ID", example=1)
    artist_name: str = Field(
        ..., alias="artistName", description="아티스트명", example="아이유"
    )
    reason: Optional[str] = Field(
        None, alias="reason", description="추천 이유", example="음악이 정말 좋아요!"
    )
    email: Optional[str] = Field(
        None, alias="email", description="이메일 주소", example="user@example.com"
    )
    user_id: Optional[int] = Field(
        None, alias="userId", description="제안한 사용자 ID", example=7
    )
    created_at: datetime = Field(
        ..., alias="createdAt", description="생성일시", example="2025-09-30T10:00:00Z"
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class ArtistSuggestionRankingDto(BaseModel):
    """아티스트 제안 순위 DTO"""

    artist_name: str = Field(
        ..., alias="artistName", description="아티스트명", example="아이유"
    )
    count: int = Field(..., alias="count", description="요청 횟수", example=15)

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {"example": {"artist_name": "아이유", "count": 15}}
