"""
채팅 메시지 모델
"""

from datetime import datetime, timezone

from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class ChatMessage(Base):
    """채팅 메시지 모델"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    channel_url = Column(String(255), nullable=False, index=True, comment="채널 URL")
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="발신자 ID"
    )
    message = Column(Text, nullable=False, comment="메시지 내용")
    message_type = Column(
        String(20),
        nullable=False,
        default="MESG",
        comment="메시지 타입 (MESG, FILE, IMAGE 등)",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
        index=True,
    )

    # 관계 설정
    user = relationship("User", foreign_keys=[user_id])
