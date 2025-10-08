from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


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
        DateTime, default=datetime.utcnow, nullable=False, comment="차단 생성 시간"
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
