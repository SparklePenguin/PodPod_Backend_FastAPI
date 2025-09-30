from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


# 그룹이나 싱글/멤버 아티스트 모델
class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    unit_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)

    # BLIP/연동 관련 식별자
    blip_unit_id = Column(Integer, nullable=False, index=True)
    blip_artist_id = Column(Integer, nullable=True, index=True)

    # 관계
    images = relationship(
        "ArtistImage",
        back_populates="artist",
        cascade="all, delete-orphan",
    )
    names = relationship(
        "ArtistName",
        back_populates="artist",
        cascade="all, delete-orphan",
    )
    # 사용자 선호 아티스트 연결
    preferred_artists = relationship(
        "PreferredArtist",
        back_populates="artist",
    )
    # 아티스트 스케줄 연결
    schedules = relationship(
        "ArtistSchedule",
        back_populates="artist",
    )
