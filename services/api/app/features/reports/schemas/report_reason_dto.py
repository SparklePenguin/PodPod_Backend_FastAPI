from pydantic import BaseModel, Field


class ReportReasonDto(BaseModel):
    """신고 사유 DTO"""

    id: int = Field(..., description="신고 사유 ID")
    code: str = Field(..., description="신고 사유 코드")
    description: str = Field(..., description="신고 사유 설명")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
