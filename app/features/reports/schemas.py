from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ReportReasonDto(BaseModel):
    """신고 사유 DTO"""

    id: int = Field(..., description="신고 사유 ID", examples=[1])
    code: str = Field(..., description="신고 사유 코드", examples=["ABUSIVE_LANGUAGE"])
    description: str = Field(
        ...,
        description="신고 사유 설명",
        examples=["욕설, 비속어 사용 - 불쾌한 언어 또는 욕설이 포함되어 있어요"],
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ReportReasonsResponse(BaseModel):
    """신고 사유 목록 응답"""

    reasons: List[ReportReasonDto] = Field(..., description="신고 사유 목록")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class CreateReportRequest(BaseModel):
    """신고 생성 요청 스키마"""

    reported_user_id: int = Field(
        ...,
        serialization_alias="reportedUserId",
        description="신고당한 사용자 ID",
        examples=[2],
    )
    report_types: List[int] = Field(
        ...,
        serialization_alias="reportTypes",
        description="신고 유형 ID 목록 (1~8, 최대 3개)",
        examples=[[1, 2]],
        min_length=1,
        max_length=3,
    )
    reason: Optional[str] = Field(
        None,
        description="신고 이유 (추가 설명)",
        examples=["불쾌한 언어를 사용했습니다."],
        max_length=500,
    )
    should_block: bool = Field(
        ...,
        serialization_alias="shouldBlock",
        description="신고와 함께 차단 여부",
        examples=[True],
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


class ReportResponse(BaseModel):
    """신고 응답 스키마"""

    id: int = Field(..., description="신고 ID", examples=[1])
    reporter_id: int = Field(
        ...,
        serialization_alias="reporterId",
        description="신고를 수행한 사용자 ID",
        examples=[1],
    )
    reported_user_id: int = Field(
        ...,
        serialization_alias="reportedUserId",
        description="신고당한 사용자 ID",
        examples=[2],
    )
    report_types: List[int] = Field(
        ..., serialization_alias="reportTypes", description="신고 유형 ID 목록"
    )
    reason: Optional[str] = Field(None, description="신고 이유 (추가 설명)")
    blocked: bool = Field(..., description="차단 여부", examples=[True])
    created_at: datetime = Field(
        ..., serialization_alias="createdAt", description="신고 생성 시간"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
