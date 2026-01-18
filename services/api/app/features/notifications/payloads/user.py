"""유저 관련 알림 Payload 정의 (팔로우 포함)"""

from .base import PodRef, UserRef


class UserFollowedPayload(UserRef):
    """팔로우 알림 payload (대상: 팔로우 받은 유저)

    UserRef의 user_id/nickname은 팔로우한 유저 정보입니다.
    """

    pass


class UserFollowedUserCreatedPodPayload(UserRef, PodRef):
    """팔로우한 유저가 파티 생성 알림 payload (대상: 팔로워)

    UserRef의 user_id/nickname은 파티를 생성한 유저(팔로잉) 정보입니다.
    """

    pass
