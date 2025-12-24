from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


# - MARK: 성향 테스트 결과 DTO
class TendencyResultDto(BaseModel):
    id: int
    type: str
    description: str
    tendency_info: Dict[str, Any] = Field(..., serialization_alias="tendencyInfo")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


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
    def from_survey_data(cls, obj):
        """survey_data에서 questions만 추출하고 questionId 추가"""
        questions = obj.survey_data.get("questions", [])
        for question in questions:
            question_id = question.get("id")
            for answer in question.get("answers", []):
                answer["questionId"] = question_id

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
    user_id: int = Field(..., serialization_alias="userId")
    tendency_type: str = Field(..., serialization_alias="tendencyType")
    answers: Dict[str, Any]
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


# - MARK: Flutter용 성향 테스트 응답 요청
class SurveyAnswer(BaseModel):
    question_id: int = Field(..., serialization_alias="questionId")
    id: int = Field(..., serialization_alias="id")


class SubmitTendencyTestRequest(BaseModel):
    answers: List[SurveyAnswer]

    model_config = {"populate_by_name": True}


# - MARK: Flutter용 성향 테스트 결과 응답
class TendencyInfo(BaseModel):
    main_type: str = Field(..., serialization_alias="mainType")
    sub_type: str = Field(..., serialization_alias="subType")
    speech_bubbles: List[str] = Field(..., serialization_alias="speechBubbles")
    one_line_descriptions: List[str] = Field(..., serialization_alias="oneLineDescriptions")
    detailed_description: str = Field(..., serialization_alias="detailedDescription")
    keywords: List[str] = Field(..., serialization_alias="keywords")

    model_config = {"populate_by_name": True}


class Tendency(BaseModel):
    type: str
    description: str
    tendency_info: TendencyInfo = Field(..., serialization_alias="tendencyInfo")

    model_config = {"populate_by_name": True}


# - MARK: 성향 테스트 응답 요청
class TendencyTestRequest(BaseModel):
    answers: Dict[str, Any] = Field(..., description="테스트 응답 데이터")


# - MARK: 성향 테스트 결과 요청
class TendencyResultRequest(BaseModel):
    tendency_type: str = Field(
        ..., description="성향 타입 (quietMate, togetherMate, fieldMate, supportMate)"
    )
