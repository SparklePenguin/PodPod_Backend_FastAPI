from pydantic import BaseModel
from typing import Optional


# - MARK: 성공 응답
class SuccessResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None


# - MARK: 에러 응답
class ErrorResponse(BaseModel):
    error_code: str
    status: int
    message: str
