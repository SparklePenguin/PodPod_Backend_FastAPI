from pydantic import BaseModel, Field
from typing import Any, Generic, TypeVar, List


# - MARK: 성공 응답
class SuccessResponse(BaseModel):
    code: int = Field(alias="code", example=200)
    message: str = Field(alias="message", example="Successfully retrieved data")
    data: Any = Field(alias="data", example=None)
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: 에러 응답
class ErrorResponse(BaseModel):
    error_code: str = Field(alias="errorCode", example="validation_error")
    status: int = Field(alias="status", example=400)
    message: str = Field(alias="message", example="Unknown error")
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# - MARK: 제네릭 페이지 응답 (Page<T>)
T = TypeVar("T")


class PageDto(BaseModel, Generic[T]):
    items: List[T]
    current_page: int = Field(alias="currentPage", example=1)
    page_size: int = Field(alias="pageSize", example=20)
    total_count: int = Field(alias="totalCount", example=0)
    total_pages: int = Field(alias="totalPages", example=0)
    has_next: bool = Field(alias="hasNext", example=False)
    has_prev: bool = Field(alias="hasPrev", example=False)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PageResponse(SuccessResponse, Generic[T]):
    data: PageDto[T]
