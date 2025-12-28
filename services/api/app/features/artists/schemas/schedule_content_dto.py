from pydantic import BaseModel, Field


class ScheduleContentDto(BaseModel):
    """스케줄 콘텐츠 DTO"""

    id: int | None = Field(default=None)
    type: str = Field(..., description="콘텐츠 유형 (video, image)")
    path: str = Field(..., description="콘텐츠 경로/URL")
    title: str | None = Field(None, description="콘텐츠 제목")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
