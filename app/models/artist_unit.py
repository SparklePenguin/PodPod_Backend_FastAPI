from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timezone


# 아티스트 유닛 모델
class ArtistUnit(Base):
    __tablename__ = "artist_units"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=True)
    type = Column(String(20), nullable=True)  # "group" 또는 "single"
    is_filter = Column(Boolean, default=True)
    is_active = Column(Boolean, default=False)  # 아티스트 이미지 디자인 유무
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # BLIP/연동 관련 식별자
    blip_unit_id = Column(Integer, nullable=False, index=True)
    blip_artist_id = Column(Integer, nullable=False, index=True)

    # 아티스트 스케줄 연결
    schedules = relationship(
        "ArtistSchedule",
        back_populates="unit",
    )
