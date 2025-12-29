from enum import Enum


class ReviewNotiSubType(Enum):
    """리뷰 알림 서브 타입"""

    # 1. 리뷰 등록됨 (대상: 모임 참여자)
    REVIEW_CREATED = (
        "📝 [nickname]님이 [party_name]에 대한 리뷰를 남겼어요!",
        ["nickname", "party_name"],
        "review_id",
    )
    # 2. 모임 종료 후 1일 후 리뷰 유도 (대상: 참여자)
    REVIEW_REMINDER_DAY = (
        "😊 오늘 [party_name] 어떠셨나요? 소중한 리뷰를 남겨보세요!",
        ["party_name"],
        "pod_id",
    )
    # 3. 리뷰 미작성자 일주일 리마인드 (대상: 리뷰 미작성자)
    REVIEW_REMINDER_WEEK = (
        "💭 [party_name] 후기가 궁금해요. 어땠는지 들려주세요!",
        ["party_name"],
        "pod_id",
    )
    # 4. 내가 참여한 파티에 다른 사람이 후기 작성 (대상: 참여자)
    REVIEW_OTHERS_CREATED = (
        "👀 같은 모임에 참여한 [nickname]님의 후기가 도착했어요!",
        ["nickname"],
        "review_id",
    )


# 하위 호환성: 레거시 이름
ReviewNotificationType = ReviewNotiSubType
