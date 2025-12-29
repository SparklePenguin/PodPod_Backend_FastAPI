from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


# 아티스트 이름 모델 (다국어 지원)
class ArtistName(Base):
    __tablename__ = "artist_names"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)
    code = Column(String(10), nullable=False, comment="언어 코드 (ko, en, ja 등)")
    name = Column(String(200), nullable=False, comment="해당 언어의 이름")
    unit_id = Column(Integer, nullable=False)

    # BLIP/연동 관련 식별자
    blip_unit_id = Column(Integer, nullable=False, index=True)
    blip_artist_id = Column(Integer, nullable=False, index=True)

    # 관계 설정
    artist = relationship("Artist", back_populates="names")
