from app.core.http_status import HttpStatus
from pydantic import BaseModel, Field
from typing import Generic, Optional, TypeVar, Dict, Any


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    data: Optional[T] = Field(
        alias="data",
        example=None,
    )
    http_status: Optional[int] = Field(
        alias="httpStatus",
        description="HTTP 상태 코드",
        example=None,
    )
    message_ko: Optional[str] = Field(
        alias="messageKo",
        description="한국어 메시지",
        example=None,
    )
    message_en: Optional[str] = Field(
        alias="messageEn",
        description="영어 메시지",
        example=None,
    )
    # 에러 정보 필드들 (실패 시에만 포함)
    error_key: Optional[str] = Field(
        alias="error",
        description="에러 코드 키",
        example=None,
    )
    error_code: Optional[int] = Field(
        alias="errorCode",
        description="숫자 에러 코드",
        example=None,
    )
    dev_note: Optional[str] = Field(
        alias="devNote",
        description="개발자 노트",
        example=None,
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @classmethod
    def ok(
        cls,
        data: T = None,
        http_status: int = 200,
        message_ko: Optional[str] = None,
        message_en: Optional[str] = None,
    ) -> "BaseResponse[T]":
        return cls(
            data=data,
            http_status=http_status,
            message_ko=message_ko,
            message_en=message_en,
            error=None,
            error_code=None,
            dev_note=None,
        )

    @classmethod
    def created(
        cls,
        data: T = None,
        message_ko: Optional[str] = None,
        message_en: Optional[str] = None,
    ) -> "BaseResponse[T]":
        return cls(
            data=data,
            http_status=201,
            message_ko=message_ko,
            message_en=message_en,
            error=None,
            error_code=None,
            dev_note=None,
        )

    @classmethod
    def error(
        cls,
        error_key: str,
        error_code: int,
        http_status: int,
        message_ko: str,
        message_en: str,
        dev_note: Optional[str] = None,
    ) -> "BaseResponse[None]":
        return cls(
            data=None,
            error=error_key,
            error_code=error_code,
            http_status=http_status,
            message_ko=message_ko,
            message_en=message_en,
            dev_note=dev_note,
        )

    @classmethod
    def error_with_code(
        cls,
        error_key: str,
        language: str = "ko",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> "BaseResponse[None]":
        """에러 코드 시스템을 사용한 에러 응답 생성"""
        from app.core.error_codes import get_error_info, get_error_response

        error_info = get_error_info(error_key, language)
        error_response = get_error_response(error_key, additional_data)

        return cls(
            data=None,
            error=error_key,
            error_code=error_info.code,
            http_status=error_info.http_status,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
            dev_note=error_response.get("dev_note"),
        )
