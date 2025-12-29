from enum import Enum


class FollowNotiSubType(Enum):
    """팔로우 알림 서브 타입"""

    # 1. 나를 팔로잉함 (대상: 팔로우된 유저)
    FOLLOWED_BY_USER = (
        "👋 [nickname]님이 당신을 팔로우했어요! 새로운 만남을 기대해 볼까요?",
        ["nickname"],
        "follow_user_id",
    )
    # 2. 내가 팔로잉한 유저가 파티 생성 (대목: 팔로워)
    FOLLOWED_USER_CREATED_POD = (
        "🎉 [nickname]님이 새로운 모임 [party_name]을 만들었어요!",
        ["nickname", "party_name"],
        "pod_id",
    )


# 하위 호환성: 레거시 이름
FollowNotificationType = FollowNotiSubType
