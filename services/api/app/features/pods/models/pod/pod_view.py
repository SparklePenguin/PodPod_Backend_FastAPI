from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class PodView(Base):
    """파티 조회수 테이블"""

    __tablename__ = "pod_views"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # 비로그인 사용자도 조회 가능
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    user_agent = Column(String(500), nullable=True)  # 브라우저 정보
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    pod = relationship("Pod", back_populates="views")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("pod_id", "user_id", "ip_address", name="uq_pod_views_pod_user_ip"),
    )
