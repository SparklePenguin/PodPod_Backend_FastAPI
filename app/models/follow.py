from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    follower_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="팔로우하는 사용자 ID",
    )
    following_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="팔로우받는 사용자 ID",
    )
    notification_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="알림 활성화 여부",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="팔로우 활성화 여부",
    )
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="팔로우 생성 시간"
    )

    # 관계 설정
    follower = relationship(
        "User", foreign_keys=[follower_id], back_populates="following"
    )
    following = relationship(
        "User", foreign_keys=[following_id], back_populates="followers"
    )

    # 유니크 제약조건: 한 사용자가 같은 사용자를 중복 팔로우할 수 없음
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="unique_follow"),
    )
