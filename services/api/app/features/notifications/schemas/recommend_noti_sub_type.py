from enum import Enum


class RecommendNotiSubType(Enum):
    """추천 알림 서브 타입"""

    # 1. 좋아요한 파티 마감 임박 (1일 전, 대상: 사용자)
    SAVED_POD_DEADLINE = (
        "🚨 [party_name] 곧 마감돼요! 신청 놓칠지도 몰라요 😥",
        ["party_name"],
        "pod_id",
    )
    # 2. 좋아요한 파티에 자리가 생겼을 때 (대상: 사용자)
    SAVED_POD_SPOT_OPENED = (
        "🎉 [party_name]에 자리가 생겼어요! 지금 신청해 보세요.",
        ["party_name"],
        "pod_id",
    )


# 하위 호환성: 레거시 이름
RecommendNotificationType = RecommendNotiSubType
