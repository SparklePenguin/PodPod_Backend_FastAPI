"""사용자 차단 및 신고 모델"""

from datetime import datetime, timezone

from app.core.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship


class UserBlock(Base):
    """사용자 차단 모델"""

    __tablename__ = "user_blocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    blocker_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="차단을 수행한 사용자 ID",
    )
    blocked_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="차단당한 사용자 ID",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="차단 생성 시간",
    )

    # 관계 설정
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocking")
    blocked = relationship(
        "User", foreign_keys=[blocked_id], back_populates="blocked_by"
    )

    # 유니크 제약조건: 한 사용자가 같은 사용자를 중복 차단할 수 없음
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="unique_user_block"),
    )


class UserReport(Base):
    """사용자 신고 모델"""

    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reporter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="신고를 수행한 사용자 ID",
    )
    reported_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="신고당한 사용자 ID",
    )
    report_types = Column(JSON, nullable=False, comment="신고 유형 ID 목록 (최대 3개)")
    reason = Column(String(500), nullable=True, comment="신고 이유 (추가 설명)")
    blocked = Column(Boolean, nullable=False, comment="신고와 함께 차단 여부")
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="신고 생성 시간",
    )

    # 관계 설정
    reporter = relationship("User", foreign_keys=[reporter_id], backref="reports_made")
    reported_user = relationship(
        "User", foreign_keys=[reported_user_id], backref="reports_received"
    )
