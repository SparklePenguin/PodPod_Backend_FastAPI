from pydantic import BaseModel, Field
from typing import Any


# - MARK: 성공 응답
class SuccessResponse(BaseModel):
    code: int
    message: str
    data: Any = None


# - MARK: 에러 응답
class ErrorResponse(BaseModel):
    error_code: str
    status: int
    message: str = "Unknown error"  # 기본값 설정


# - MARK: 페이지네이션 응답
class PaginationDto(BaseModel):
    current_page: int = Field(alias="current_page", example=1)
    page_size: int = Field(alias="page_size", example=20)
    total_count: int = Field(alias="total_count", example=0)
    total_pages: int = Field(alias="total_pages", example=0)
    has_next: bool = Field(alias="has_next", example=False)
    has_prev: bool = Field(
        alias="has_prev",
        example=False,
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
