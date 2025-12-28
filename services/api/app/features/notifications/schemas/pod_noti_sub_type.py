from enum import Enum


class PodNotiSubType(Enum):
    """파티 알림 서브 타입"""

    # 1. 파티 참여 요청 (대상: 파티장)
    POD_JOIN_REQUEST = (
        "[nickname]님이 모임에 참여를 요청했어요. 확인해 보세요!",
        ["nickname"],
        "pod_id",
    )
    # 2. 참여 요청 승인 (대상: 요청자)
    POD_REQUEST_APPROVED = (
        "👋 [party_name] 참여가 확정되었어요! 채팅방에서 인사 나눠보세요.",
        ["party_name"],
        "pod_id",
    )
    # 3. 참여 요청 거절 (대상: 요청자)
    POD_REQUEST_REJECTED = (
        "😢 아쉽게도 [party_name] 참여가 어렵게 되었어요. 다른 모임도 둘러보세요.",
        ["party_name"],
        "pod_id",
    )
    # 4. 파티에 새로운 유저 참여 (대상: 기존 파티원들)
    POD_NEW_MEMBER = (
        "👋 새로운 파티원 [nickname]님이 [party_name] 모임에 함께하게 되었어요!",
        ["nickname", "party_name"],
        "pod_id",
    )
    # 5. 파티 내용 수정 (대상: 파티장 & 파티원)
    POD_UPDATED = (
        "🛠️ [party_name] 모임 정보가 변경되었어요. 지금 확인해 보세요.",
        ["party_name"],
        "pod_id",
    )
    # 6. 파티 확정 (대상: 파티원)
    POD_CONFIRMED = (
        "✅ 모임이 드디어 확정! [party_name]에 함께할 준비 되셨죠?",
        ["party_name"],
        "pod_id",
    )
    # 7. 파티 취소 (대상: 파티원)
    POD_CANCELED = ("😢 [party_name] 모임이 취소되었어요.", ["party_name"], "pod_id")
    # 8. 신청한 파티 시작 1시간 전 (대상: 사용자)
    POD_START_SOON = (
        "⏰ [party_name] 모임이 한 시간 뒤 시작돼요. 준비되셨나요?",
        ["party_name"],
        "pod_id",
    )
    # 9. 파티 마감 임박 (대상: 파티장)
    POD_LOW_ATTENDANCE = (
        "😢 [party_name] 오늘 파티가 확정되지 않으면 취소돼요. 시간이 더 필요하다면 일정을 수정할 수 있어요!",
        ["party_name"],
        "pod_id",
    )
    # 10. 파티 취소 임박 (대상: 파티장)
    POD_CANCELED_SOON = (
        "😢 [party_name] 팟티가 곧 취소돼요!",
        ["party_name"],
        "pod_id",
    )


# 하위 호환성: 레거시 이름
PodNotificationType = PodNotiSubType
