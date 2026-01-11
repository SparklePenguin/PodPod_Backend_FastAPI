"""
하위 호환성을 위한 wrapper 모듈

새 위치: app.core.exceptions.loader
"""

from app.core.exceptions.loader import (
    discover_exception_handlers,
    register_exception_handlers,
)

__all__ = [
    "discover_exception_handlers",
    "register_exception_handlers",
]
