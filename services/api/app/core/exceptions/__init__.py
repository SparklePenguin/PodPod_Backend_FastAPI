"""
예외 처리 모듈

이 모듈은 에러 코드 관리, 예외 클래스, 핸들러를 포함합니다.
"""

# 에러 레지스트리
from .registry import (
    ERROR_CODES,
    ErrorInfo,
    get_error_codes,
    get_error_info,
    get_error_response,
    raise_error,
)

# 예외 클래스
from .base import BusinessException, DomainException

# 핸들러
from .handlers import (
    business_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    value_error_handler,
)

# 로더
from .loader import discover_exception_handlers, register_exception_handlers

__all__ = [
    # Registry
    "ERROR_CODES",
    "ErrorInfo",
    "get_error_codes",
    "get_error_info",
    "get_error_response",
    "raise_error",
    # Base
    "BusinessException",
    "DomainException",
    # Handlers
    "http_exception_handler",
    "validation_exception_handler",
    "value_error_handler",
    "business_exception_handler",
    "general_exception_handler",
    # Loader
    "discover_exception_handlers",
    "register_exception_handlers",
]
