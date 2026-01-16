"""유저 관련 알림 이벤트 (팔로우 포함)"""

from enum import Enum


class UserEvent(str, Enum):
    """유저 알림 이벤트"""

    FOLLOWED = "USER_FOLLOWED"  # 나를 팔로잉함 (대상: 팔로우된 유저)
    FOLLOWED_USER_CREATED_POD = "USER_FOLLOWED_USER_CREATED_POD"  # 내가 팔로잉한 유저가 파티 생성 (대상: 팔로워)
