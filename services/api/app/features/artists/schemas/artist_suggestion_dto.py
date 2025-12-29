from datetime import datetime

from pydantic import BaseModel, Field


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
