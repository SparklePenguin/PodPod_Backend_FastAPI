from app.core.database import Base
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ArtistSchedule(Base):
    """아티스트 스케줄 엔터티"""

    __tablename__ = "artist_schedules"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(
        Integer,
        ForeignKey("artists.id"),
        nullable=True,
        index=True,
        comment="아티스트 ID",
    )
    unit_id = Column(
        Integer,
        ForeignKey("artist_units.id"),
        nullable=True,
        index=True,
        comment="아티스트 유닛 ID",
    )
    artist_ko_name = Column(
        String(100), nullable=False, index=True, comment="아티스트 한글명"
    )
    type = Column(Integer, nullable=False, comment="일정 유형")
    start_time = Column(
        BigInteger, nullable=False, index=True, comment="일정 시작 시간 (밀리초)"
    )
    end_time = Column(BigInteger, nullable=False, comment="일정 종료 시간 (밀리초)")
    text = Column(Text, nullable=True, comment="일정 상세 설명")
    title = Column(String(500), nullable=False, comment="일정 제목")
    channel = Column(String(100), nullable=True, comment="방송 채널")
    location = Column(String(200), nullable=True, comment="장소")

    # 메타데이터
    created_at = Column(DateTime, default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), comment="수정일시"
    )

    # 관계 설정
    artist = relationship("Artist", back_populates="schedules")
    unit = relationship("ArtistUnit", back_populates="schedules")
    members = relationship(
        "ScheduleMember", back_populates="schedule", cascade="all, delete-orphan"
    )
    contents = relationship(
        "ScheduleContent", back_populates="schedule", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ArtistSchedule(id={self.id}, artist='{self.artist_ko_name}', title='{self.title}')>"
