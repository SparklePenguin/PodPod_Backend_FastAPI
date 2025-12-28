from pydantic import BaseModel, Field


class ScheduleMemberCreateRequest(BaseModel):
    """스케줄 멤버 생성 요청"""

    ko_name: str = Field(..., description="멤버 한글명")
    en_name: str = Field(..., description="멤버 영문명")
    artist_id: int | None = Field(None, description="아티스트 ID")
