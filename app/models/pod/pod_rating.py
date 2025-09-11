from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class PodRating(Base):
    """파티 평점 테이블"""

    __tablename__ = "pod_ratings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5점 평점
    review = Column(String(500), nullable=True)  # 리뷰 내용
    created_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    pod = relationship("Pod", back_populates="ratings")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("pod_id", "user_id", name="uq_pod_ratings_pod_user"),
    )
