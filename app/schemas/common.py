from pydantic import BaseModel
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
