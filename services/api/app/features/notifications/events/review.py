"""리뷰 관련 알림 이벤트"""

from enum import Enum


class ReviewEvent(str, Enum):
    """리뷰 알림 이벤트"""

    CREATED = "REVIEW_CREATED"  # 리뷰 등록됨 (대상: 모임 참여자)
    REMINDER_DAY = "REVIEW_REMINDER_DAY"  # 모임 종료 후 1일 후 리뷰 유도 (대상: 참여자)
    REMINDER_WEEK = "REVIEW_REMINDER_WEEK"  # 리뷰 미작성자 일주일 리마인드 (대상: 리뷰 미작성자)
    OTHERS_CREATED = "REVIEW_OTHERS_CREATED"  # 내가 참여한 파티에 다른 사람이 후기 작성 (대상: 참여자)
