"""파티(Pod) 관련 알림 이벤트"""

from enum import Enum


class PodEvent(str, Enum):
    """파티 알림 이벤트"""

    # 참여 관련
    JOIN_REQUESTED = "POD_JOIN_REQUESTED"  # 파티 참여 요청 (대상: 파티장)
    JOIN_APPROVED = "POD_JOIN_APPROVED"  # 참여 요청 승인 (대상: 요청자)
    JOIN_REJECTED = "POD_JOIN_REJECTED"  # 참여 요청 거절 (대상: 요청자)
    MEMBER_JOINED = "POD_MEMBER_JOINED"  # 새로운 유저 참여 (대상: 기존 파티원들)

    # 파티 상태 변경
    UPDATED = "POD_UPDATED"  # 파티 내용 수정 (대상: 파티장 & 파티원)
    CONFIRMED = "POD_CONFIRMED"  # 파티 확정 (대상: 파티원)
    CANCELED = "POD_CANCELED"  # 파티 취소 (대상: 파티원)
    STARTING_SOON = "POD_STARTING_SOON"  # 파티 시작 1시간 전 (대상: 사용자)
    LOW_ATTENDANCE = "POD_LOW_ATTENDANCE"  # 파티 마감 임박 (대상: 파티장)
    CANCELED_SOON = "POD_CANCELED_SOON"  # 파티 취소 임박 (대상: 파티장)
    COMPLETED = "POD_COMPLETED"  # 파티 완료 (대상: 참여자들)

    # 파티 인기/상태 알림
    LIKES_THRESHOLD = "POD_LIKES_THRESHOLD"  # 좋아요 10개 이상 (대상: 파티장)
    VIEWS_THRESHOLD = "POD_VIEWS_THRESHOLD"  # 조회수 10회 이상 (대상: 파티장)
    CAPACITY_FULL = "POD_CAPACITY_FULL"  # 정원 가득 참 (대상: 파티장)
