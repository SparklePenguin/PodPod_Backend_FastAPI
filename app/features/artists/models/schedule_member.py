from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ScheduleMember(Base):
    """스케줄 참여 멤버 엔터티"""

    __tablename__ = "schedule_members"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(
        Integer, ForeignKey("artist_schedules.id"), nullable=False, comment="스케줄 ID"
    )
    artist_id = Column(
        Integer,
        ForeignKey("artists.id"),
        nullable=True,
        index=True,
        comment="아티스트 ID",
    )
    ko_name = Column(String(50), nullable=False, comment="멤버 한글명")
    en_name = Column(String(50), nullable=False, comment="멤버 영문명")

    # 메타데이터
    created_at = Column(DateTime, default=func.now(), comment="생성일시")

    # 관계 설정
    schedule = relationship("ArtistSchedule", back_populates="members")
    artist = relationship("Artist")

    def __repr__(self):
        return f"<ScheduleMember(id={self.id}, ko_name='{self.ko_name}', en_name='{self.en_name}')>"
