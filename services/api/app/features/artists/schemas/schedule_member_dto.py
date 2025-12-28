from pydantic import BaseModel, Field


class ScheduleMemberDto(BaseModel):
    """스케줄 멤버 DTO"""

    id: int | None = Field(default=None)
    ko_name: str = Field(..., alias="koName", description="멤버 한글명")
    en_name: str = Field(..., alias="enName", description="멤버 영문명")
    artist_id: int | None = Field(None, alias="artistId", description="아티스트 ID")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
