from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class PodMember(Base):
    __tablename__ = "pod_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pod_id = Column(Integer, ForeignKey("pods.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="owner")
    joined_at = Column(DateTime, default=datetime.now(timezone.utc))

    pod = relationship("Pod", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("pod_id", "user_id", name="uq_pod_members_pod_user"),
    )
