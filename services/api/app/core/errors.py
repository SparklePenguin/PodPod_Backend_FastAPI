"""
하위 호환성을 위한 wrapper 모듈

새 위치: app.core.exceptions.registry
"""

from app.core.exceptions.registry import (
    ERROR_CODES,
    ERRORS_JSON_PATH,
    ErrorInfo,
    get_error_codes,
    get_error_info,
    get_error_response,
    raise_error,
)

__all__ = [
    "ERROR_CODES",
    "ERRORS_JSON_PATH",
    "ErrorInfo",
    "get_error_codes",
    "get_error_info",
    "get_error_response",
    "raise_error",
]
