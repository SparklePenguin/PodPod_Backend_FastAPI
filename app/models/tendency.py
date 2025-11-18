from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


# 성향 테스트 결과 모델
class TendencyResult(Base):
    __tablename__ = "tendency_results"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(
        String(50), nullable=False, unique=True
    )  # quietMate, togetherMate, fieldMate, supportMate
    description = Column(String(200), nullable=False)

    # JSON 형태로 저장할 상세 정보
    tendency_info = Column(
        JSON, nullable=False
    )  # mainType, subType, speechBubbles, oneLineDescriptions, detailedDescription, keywords

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# 성향 테스트 설문 모델
class TendencySurvey(Base):
    __tablename__ = "tendency_surveys"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)

    # JSON 형태로 저장할 설문 데이터
    survey_data = Column(JSON, nullable=False)  # questions 배열

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# 사용자 성향 테스트 결과 모델
class UserTendencyResult(Base):
    __tablename__ = "user_tendency_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tendency_type = Column(
        String(50), nullable=False
    )  # quietMate, togetherMate, fieldMate, supportMate

    # 테스트 응답 데이터 (JSON)
    answers = Column(JSON, nullable=False)  # 사용자의 답변 데이터

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
