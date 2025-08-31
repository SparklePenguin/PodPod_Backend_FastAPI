from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# - MARK: 성향 테스트 결과 DTO
class TendencyResultDto(BaseModel):
    id: int
    type: str
    description: str
    tendency_info: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# - MARK: 성향 테스트 설문 DTO
class TendencySurveyDto(BaseModel):
    id: int
    name: str = "tendency_survey"
    title: str
    questions: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        # survey_data에서 questions만 추출하고 question_id 추가
        questions = obj.survey_data.get("questions", [])
        for question in questions:
            question_id = question.get("id")
            for answer in question.get("answers", []):
                answer["question_id"] = question_id

        return cls(
            id=obj.id,
            name="tendency_survey",
            title=obj.survey_data.get("title", ""),
            questions=questions,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


# - MARK: 사용자 성향 테스트 결과 DTO
class UserTendencyResultDto(BaseModel):
    id: int
    user_id: int
    tendency_type: str
    answers: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# - MARK: 성향 테스트 응답 요청
class TendencyTestRequest(BaseModel):
    answers: Dict[str, Any] = Field(..., description="테스트 응답 데이터")


# - MARK: 성향 테스트 결과 요청
class TendencyResultRequest(BaseModel):
    tendency_type: str = Field(
        ..., description="성향 타입 (quietMate, togetherMate, fieldMate, supportMate)"
    )
