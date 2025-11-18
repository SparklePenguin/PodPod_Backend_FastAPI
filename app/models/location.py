from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Location(Base):
    """지역 정보 모델"""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    main_location = Column(
        String(50), nullable=False, comment="주요 지역 (예: 서울, 경기)"
    )
    sub_locations = Column(
        Text, nullable=False, comment="세부 지역들 (JSON 형태로 저장)"
    )

    def __repr__(self):
        return f"<Location(id={self.id}, main_location='{self.main_location}')>"
