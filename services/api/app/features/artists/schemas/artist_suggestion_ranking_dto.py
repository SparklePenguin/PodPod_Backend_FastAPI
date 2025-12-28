from pydantic import BaseModel, Field


class ArtistSuggestionRankingDto(BaseModel):
    """아티스트 제안 순위 DTO"""

    artist_name: str = Field(..., alias="artistName", description="아티스트명")
    count: int = Field(..., description="요청 횟수")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {"example": {"artist_name": "아이유", "count": 15}}
