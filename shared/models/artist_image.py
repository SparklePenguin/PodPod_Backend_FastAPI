from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


# 아티스트 이미지 모델
class ArtistImage(Base):
    __tablename__ = "artist_images"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)
    path = Column(String(500), nullable=True, comment="image.path")
    file_id = Column(String(100), nullable=True, comment="image.fileId (null로 설정)")
    is_animatable = Column(Boolean, default=False, comment="image.isAnimatable")
    size = Column(String(50), nullable=True, comment="image.size")
    unit_id = Column(Integer, nullable=False, comment="원본 JSON의 unitId")

    # BLIP/연동 관련 식별자
    blip_unit_id = Column(Integer, nullable=False, index=True)
    blip_artist_id = Column(Integer, nullable=False, index=True)

    # 관계 설정
    artist = relationship("Artist", back_populates="images")
