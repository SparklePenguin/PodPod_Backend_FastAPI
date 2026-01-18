"""시스템 알림 이벤트 (추천 등)"""

from enum import Enum


class SystemEvent(str, Enum):
    """시스템 알림 이벤트"""

    # 추천/좋아요한 파티 관련
    SAVED_POD_DEADLINE = "SYSTEM_SAVED_POD_DEADLINE"  # 좋아요한 파티 마감 임박 (1일 전)
    SAVED_POD_SPOT_OPENED = "SYSTEM_SAVED_POD_SPOT_OPENED"  # 좋아요한 파티에 자리가 생겼을 때
