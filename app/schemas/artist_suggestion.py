from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class ArtistSuggestionCreateRequest(BaseModel):
    """아티스트 제안 생성 요청"""

    artist_name: str = Field(
        ..., min_length=1, max_length=100, description="아티스트명", example="아이유"
    )
    reason: Optional[str] = Field(
        None, max_length=1000, description="추천 이유", example="음악이 정말 좋아요!"
    )
    email: Optional[EmailStr] = Field(
        None, description="이메일 주소", example="user@example.com"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "artist_name": "아이유",
                "reason": "음악이 정말 좋아요! 많은 사람들이 좋아할 것 같습니다.",
                "email": "user@example.com",
            }
        }


class ArtistSuggestionNameOnlyRequest(BaseModel):
    """아티스트명만으로 제안하는 요청"""

    artist_name: str = Field(
        ..., min_length=1, max_length=100, description="아티스트명", example="아이유"
    )

    class Config:
        json_schema_extra = {"example": {"artist_name": "아이유"}}


class ArtistSuggestionDto(BaseModel):
    """아티스트 제안 응답 DTO"""

    id: int = Field(..., description="제안 ID", example=1)
    artist_name: str = Field(..., description="아티스트명", example="아이유")
    reason: Optional[str] = Field(
        None, description="추천 이유", example="음악이 정말 좋아요!"
    )
    email: Optional[str] = Field(
        None, description="이메일 주소", example="user@example.com"
    )
    created_at: datetime = Field(
        ..., description="생성일시", example="2025-09-30T10:00:00Z"
    )

    class Config:
        from_attributes = True


class ArtistSuggestionRankingDto(BaseModel):
    """아티스트 제안 순위 DTO"""

    artist_name: str = Field(..., description="아티스트명", example="아이유")
    count: int = Field(..., description="요청 횟수", example=15)

    class Config:
        json_schema_extra = {"example": {"artist_name": "아이유", "count": 15}}
