from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base


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
    report_types = Column(
        JSON,
        nullable=False,
        comment="신고 유형 ID 목록 (최대 3개)",
    )
    reason = Column(
        String(500),
        nullable=True,
        comment="신고 이유 (추가 설명)",
    )
    blocked = Column(
        Boolean,
        nullable=False,
        comment="신고와 함께 차단 여부",
    )
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
