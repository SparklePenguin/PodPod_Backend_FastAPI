from typing import List

from pydantic import BaseModel, Field, field_validator


class CreateReportRequest(BaseModel):
    """신고 생성 요청 스키마"""

    reported_user_id: int = Field(
        ..., alias="reportedUserId", description="신고당한 사용자 ID"
    )
    report_types: List[int] = Field(
        ...,
        alias="reportTypes",
        description="신고 유형 ID 목록 (1~8, 최대 3개)",
        min_length=1,
        max_length=3,
    )
    reason: str | None = Field(
        None, description="신고 이유 (추가 설명)", max_length=500
    )
    should_block: bool = Field(
        ..., alias="shouldBlock", description="신고와 함께 차단 여부"
    )

    @field_validator("report_types")
    @classmethod
    def validate_report_types(cls, v):
        """신고 유형 ID 유효성 검증"""
        if not v:
            raise ValueError("신고 유형을 최소 1개 이상 선택해야 합니다.")
        if len(v) > 3:
            raise ValueError("신고 유형은 최대 3개까지 선택 가능합니다.")
        for report_type in v:
            if report_type < 1 or report_type > 8:
                raise ValueError("신고 유형 ID는 1~8 사이여야 합니다.")
        # 중복 제거
        if len(v) != len(set(v)):
            raise ValueError("중복된 신고 유형은 선택할 수 없습니다.")
        return v

    model_config = {
        "populate_by_name": True,
    }
