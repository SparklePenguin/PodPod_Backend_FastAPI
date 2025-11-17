from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class PodImage(Base):
    """파티 이미지 테이블"""

    __tablename__ = "pod_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)  # 이미지 URL
    thumbnail_url = Column(String(500), nullable=True)  # 썸네일 URL
    display_order = Column(Integer, nullable=False, default=0)  # 표시 순서
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    pod = relationship("Pod", back_populates="images")
