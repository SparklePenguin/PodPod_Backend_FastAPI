from sqlalchemy import Boolean, Column, ForeignKey, Integer, Time
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserNotificationSettings(Base):
    """사용자 알림 설정 모델"""

    __tablename__ = "user_notification_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )  # 사용자 ID (1:1 관계)

    # 카테고리별 알림 설정
    notice_enabled = Column(
        Boolean, default=True, nullable=False, comment="공지 알림 활성화"
    )
    pod_enabled = Column(
        Boolean, default=True, nullable=False, comment="파티 알림 활성화"
    )
    community_enabled = Column(
        Boolean, default=True, nullable=False, comment="커뮤니티 알림 활성화"
    )
    chat_enabled = Column(
        Boolean, default=True, nullable=False, comment="채팅 알림 활성화"
    )

    # 방해금지 시간 설정
    do_not_disturb_enabled = Column(
        Boolean, default=False, nullable=False, comment="방해금지 모드 활성화"
    )
    do_not_disturb_start = Column(
        Time, nullable=True, comment="방해금지 시작 시간 (HH:MM)"
    )
    do_not_disturb_end = Column(
        Time, nullable=True, comment="방해금지 종료 시간 (HH:MM)"
    )

    # 마케팅 수신 동의
    marketing_enabled = Column(
        Boolean, default=False, nullable=False, comment="마케팅 알림 수신 동의"
    )

    # 관계 설정
    user = relationship("User", back_populates="notification_settings")
