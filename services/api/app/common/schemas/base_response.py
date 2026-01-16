from typing import Any, Dict, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    data: T | None = Field(default=None)
    http_status: int | None = Field(
        default=None, alias="httpStatus", description="HTTP 상태 코드"
    )
    message_ko: str | None = Field(
        default=None, alias="messageKo", description="한국어 메시지"
    )
    message_en: str | None = Field(
        default=None, alias="messageEn", description="영어 메시지"
    )
    error_key: str | None = Field(
        default=None, alias="error", description="에러 코드 키"
    )
    error_code: int | None = Field(
        default=None, alias="errorCode", description="숫자 에러 코드"
    )
    dev_note: str | None = Field(
        default=None, alias="devNote", description="개발자 노트"
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
        message_ko: str | None = None,
        message_en: str | None = None,
    ) -> "BaseResponse[T]":
        return cls(
            data=data,
            http_status=http_status,
            message_ko=message_ko,
            message_en=message_en,
        )

    @classmethod
    def error(
        cls,
        http_status: int,
        error_key: str,
        error_code: int,
        message_ko: str,
        message_en: str,
        dev_note: str | None = None,
    ) -> "BaseResponse[T]":
        return cls(
            http_status=http_status,
            message_ko=message_ko,
            message_en=message_en,
            error_key=error_key,
            error_code=error_code,
            dev_note=dev_note,
        )

    @classmethod
    def error_with_code(
        cls,
        error_key: str,
        language: str = "ko",
        additional_data: Dict[str, Any] | None = None,
    ) -> "BaseResponse[T]":
        """에러 코드 시스템을 사용한 에러 응답 생성"""
        from app.core.exceptions import get_error_info, get_error_response

        error_info = get_error_info(error_key, language)
        error_response = get_error_response(error_key, additional_data=additional_data)

        return cls(
            http_status=error_info.http_status,
            message_ko=error_info.message_ko,
            message_en=error_info.message_en,
            error_key=error_key,
            error_code=error_info.code,
            dev_note=error_response.get("dev_note"),
        )
