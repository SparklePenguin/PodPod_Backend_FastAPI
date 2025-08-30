from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


# 사용자와 아티스트 관계 모델
class PreferredArtist(Base):
    __tablename__ = "preferred_artists"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), primary_key=True)

    user = relationship("User", back_populates="preferred_artists")
    artist = relationship("Artist", back_populates="preferred_artists")
