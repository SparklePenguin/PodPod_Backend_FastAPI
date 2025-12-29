from enum import Enum


class PodStatusNotiSubType(Enum):
    """파티 상태 알림 서브 타입"""

    # 1. 좋아요 수 10개 이상 달성 (대상: 파티장)
    POD_LIKES_THRESHOLD = (
        "🎉 [party_name] 모임에 좋아요가 10개 이상 쌓였어요!",
        ["party_name"],
        "pod_id",
    )
    # 2. 조회수 10회 이상 달성 (대상: 파티장)
    POD_VIEWS_THRESHOLD = (
        "🔥 [party_name]에 관심이 몰리고 있어요. 인기 모임이 될지도 몰라요!",
        ["party_name"],
        "pod_id",
    )
    # 3. 파티 완료 (대상: 참여자들)
    POD_COMPLETED = (
        "🎉 [party_name] 모임이 완료되었습니다! 즐거운 시간 보내셨나요?",
        ["party_name"],
        "pod_id",
    )
    # 4. 파티 정원 가득 참 (대상: 파티장)
    POD_CAPACITY_FULL = (
        "👋 [party_name] 참여 인원이 모두 모였어요!",
        ["party_name"],
        "pod_id",
    )


# 하위 호환성: 레거시 이름
PodStatusNotificationType = PodStatusNotiSubType
