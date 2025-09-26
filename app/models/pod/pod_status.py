from enum import Enum


class PodStatus(str, Enum):
    """파티 상태 열거형"""

    RECRUITING = "RECRUITING"  # 모집중
    FULL = "FULL"  # 인원 가득참
    COMPLETED = "COMPLETED"  # 모집 완료
    CLOSED = "CLOSED"  # 종료
