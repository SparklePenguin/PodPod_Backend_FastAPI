from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PodReview(Base):
    __tablename__ = "pod_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(
        Integer,
        ForeignKey("pods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="파티 ID",
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="작성자 ID",
    )
    rating = Column(
        Integer,
        nullable=False,
        comment="별점 (1-5)",
    )
    content = Column(
        Text,
        nullable=False,
        comment="후기 내용",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="작성 시간",
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="수정 시간",
    )

    # 관계 설정
    pod = relationship("Pod", back_populates="reviews")
    user = relationship("User", back_populates="pod_reviews")
