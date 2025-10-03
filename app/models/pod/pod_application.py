from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Enum,
    DateTime,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class ApplicationStatus:
    PENDING = "pending"  # 대기 중
    APPROVED = "approved"  # 승인됨
    REJECTED = "rejected"  # 거절됨


class PodApplication(Base):
    """파티 참여 신청서 모델"""

    __tablename__ = "pod_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=True, comment="참여 신청 메시지")
    status = Column(
        String(20),
        nullable=False,
        default=ApplicationStatus.PENDING,
        comment="신청 상태 (pending, approved, rejected)",
    )
    applied_at = Column(
        Integer,
        nullable=False,
        default=lambda: int(datetime.now(timezone.utc).timestamp()),
        comment="신청 시간 (Unix timestamp)",
    )
    reviewed_at = Column(
        Integer,
        nullable=True,
        comment="검토 시간 (Unix timestamp)",
    )
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="검토한 사용자 ID (파티 개설자)",
    )

    # 관계 설정
    pod = relationship("Pod", back_populates="applications")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        # 같은 파티에 같은 사용자가 중복 신청할 수 없도록 제약
        {"extend_existing": True}
    )
