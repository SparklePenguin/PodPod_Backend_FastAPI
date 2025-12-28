from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class PreferredArtist(Base):
    """사용자와 아티스트 관계 모델"""

    __tablename__ = "preferred_artists"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)

    user = relationship("User", back_populates="preferred_artists")
    artist = relationship("Artist", back_populates="preferred_artists")
