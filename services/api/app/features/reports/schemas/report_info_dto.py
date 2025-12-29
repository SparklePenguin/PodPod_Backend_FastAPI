import datetime
from typing import List

from pydantic import BaseModel, Field


class ReportInfoDto(BaseModel):
    """신고 응답 스키마"""

    id: int = Field(..., description="신고 ID")
    reporter_id: int = Field(
        ..., alias="reporterId", description="신고를 수행한 사용자 ID"
    )
    reported_user_id: int = Field(
        ..., alias="reportedUserId", description="신고당한 사용자 ID"
    )
    report_types: List[int] = Field(
        ..., alias="reportTypes", description="신고 유형 ID 목록"
    )
    reason: str | None = Field(None, description="신고 이유 (추가 설명)")
    blocked: bool = Field(..., description="차단 여부")
    created_at: datetime.datetime = Field(
        ..., alias="createdAt", description="신고 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
