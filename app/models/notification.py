"""
알림 모델
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Notification(Base):
    """알림 모델"""

    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )  # 받는 사람
    related_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # 관련 유저 (알림 발생시킨 유저)
    related_pod_id = Column(
        Integer, ForeignKey("pods.id"), nullable=True, index=True
    )  # 관련 파티

    # 알림 내용
    title = Column(String(100), nullable=False)  # 알림 제목
    body = Column(Text, nullable=False)  # 알림 내용

    # 알림 타입 및 관련 정보
    notification_type = Column(
        String(50), nullable=False, index=True
    )  # PodNotificationType, FollowNotificationType 등
    notification_value = Column(
        String(50), nullable=False
    )  # POD_JOIN_REQUEST, FOLLOWED_BY_USER 등
    related_id = Column(
        String(50), nullable=True
    )  # pod_id, review_id, follow_user_id 등
    category = Column(
        String(20), nullable=False, index=True, default="pod"
    )  # pod, community, notice

    # 읽음 상태
    is_read = Column(Boolean, default=False, nullable=False, index=True)  # 읽음 여부
    read_at = Column(DateTime, nullable=True)  # 읽은 시간

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
        index=True,
    )

    # 관계 설정
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    related_user = relationship("User", foreign_keys=[related_user_id])
    related_pod = relationship("Pod", foreign_keys=[related_pod_id])
