from app.core.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ScheduleContent(Base):
    """스케줄 관련 콘텐츠 엔터티"""

    __tablename__ = "schedule_contents"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(
        Integer, ForeignKey("artist_schedules.id"), nullable=False, comment="스케줄 ID"
    )
    type = Column(String(20), nullable=False, comment="콘텐츠 유형 (video, image)")
    path = Column(String(1000), nullable=False, comment="콘텐츠 경로/URL")
    title = Column(String(500), nullable=True, comment="콘텐츠 제목")

    # 메타데이터
    created_at = Column(DateTime, default=func.now(), comment="생성일시")

    # 관계 설정
    schedule = relationship("ArtistSchedule", back_populates="contents")

    def __repr__(self):
        return (
            f"<ScheduleContent(id={self.id}, type='{self.type}', path='{self.path}')>"
        )
