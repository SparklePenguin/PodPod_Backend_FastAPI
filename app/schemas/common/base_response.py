from app.core.http_status import HttpStatus
from pydantic import BaseModel, Field
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    code: HttpStatus = Field(
        alias="code",
        example=HttpStatus.OK.value,
    )
    message: Optional[str] = Field(
        alias="message",
        example=HttpStatus.OK.phrase,
    )
    data: Optional[T] = Field(
        alias="data",
        example=None,
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @classmethod
    def ok(
        cls,
        data: T,
        code: HttpStatus = HttpStatus.OK,
    ) -> "BaseResponse[T]":
        return cls(
            code=code.value,
            message=code.phrase,
            data=data,
        )

    @classmethod
    def error(
        cls,
        code: HttpStatus.BAD_REQUEST,
        message: Optional[str] = None,
    ) -> "BaseResponse[None]":
        return cls(
            code=code.value,
            message=message or code.phrase,
            data=None,
        )
