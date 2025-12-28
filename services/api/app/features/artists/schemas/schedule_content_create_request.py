from pydantic import BaseModel, Field


class ScheduleContentCreateRequest(BaseModel):
    """스케줄 콘텐츠 생성 요청"""

    type: str = Field(..., description="콘텐츠 유형 (video, image)")
    path: str = Field(..., description="콘텐츠 경로/URL")
    title: str | None = Field(None, description="콘텐츠 제목")
