"""Application 관련 모델들"""

from datetime import datetime, timezone
from enum import Enum

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


# - MARK: Application Status Enum
class ApplicationStatus(str, Enum):
    """신청 상태 열거형"""

    PENDING = "pending"  # 대기 중
    APPROVED = "approved"  # 승인됨
    REJECTED = "rejected"  # 거절됨


# - MARK: Application Model (간단한 버전 - PodApplDto에 대응)
class Application(Base):
    """파티 참여 신청서 모델 (간단한 버전)"""

    __tablename__ = "pod_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(
        SQLEnum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.PENDING,
        comment="신청 상태 (pending, approved, rejected)",
    )
    applied_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="신청 시간",
    )
    is_hidden = Column(
        Boolean, nullable=False, default=False, comment="파티장이 숨김 처리했는지 여부"
    )

    # 관계 설정 (리스트용 - 최소화)
    pod = relationship("Pod", back_populates="applications")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")

    __table_args__ = (
        # 같은 파티에 같은 사용자가 중복 신청할 수 없도록 제약
        {"extend_existing": True}
    )


# - MARK: Application Detail Model (상세 버전 - PodApplDetailDto에 대응)
class ApplicationDetail(Application):
    """파티 참여 신청서 모델 (상세 버전)"""

    __tablename__ = "pod_applications"

    message = Column(Text, nullable=True, comment="참여 신청 메시지")
    reviewed_at = Column(DateTime, nullable=True, comment="검토 시간")
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="검토한 사용자 ID (파티 개설자)",
    )

    # 관계 설정 (상세용)
    reviewer = relationship("User", foreign_keys=[reviewed_by])
