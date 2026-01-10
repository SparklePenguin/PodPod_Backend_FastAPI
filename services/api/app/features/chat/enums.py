"""
채팅 관련 Enum
"""

from enum import Enum


class MessageType(str, Enum):
    """메시지 타입"""

    TEXT = "TEXT"  # 일반 텍스트 메시지
    FILE = "FILE"  # 파일 메시지
    IMAGE = "IMAGE"  # 이미지 메시지
    SYSTEM = "SYSTEM"  # 시스템 메시지
