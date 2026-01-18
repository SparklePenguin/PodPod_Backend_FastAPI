"""성향 테스트 관련 스키마"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class TendencyInfoDto(BaseModel):
    """성향 정보 DTO"""

    main_type: str = Field(..., alias="mainType")
    sub_type: str = Field(..., alias="subType")
    speech_bubbles: List[str] = Field(..., alias="speechBubbles")
    one_line_descriptions: List[str] = Field(..., alias="oneLineDescriptions")
    detailed_description: str = Field(..., alias="detailedDescription")
    keywords: List[str] = Field(...)

    model_config = {"populate_by_name": True}


class TendencyDto(BaseModel):
    """성향 테스트 결과 응답"""

    type: str
    description: str
    tendency_info: TendencyInfoDto = Field(..., alias="tendencyInfo")

    model_config = {"populate_by_name": True}


class TendencySurveyDto(BaseModel):
    """성향 테스트 설문 DTO"""

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


class SurveyAnswerDto(BaseModel):
    """성향 테스트 답변 스키마"""

    question_id: int = Field(..., alias="questionId")
    id: int = Field(...)

    model_config = {"populate_by_name": True}


class TendencyResultDto(BaseModel):
    """성향 테스트 결과 DTO"""

    id: int
    type: str
    description: str
    tendency_info: Dict[str, Any] = Field(..., alias="tendencyInfo")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserTendencyResultDto(BaseModel):
    """사용자 성향 테스트 결과 DTO"""

    id: int
    user_id: int = Field(..., alias="userId")
    tendency_type: str = Field(..., alias="tendencyType")
    answers: Dict[str, Any]
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SubmitTendencyTestRequest(BaseModel):
    """성향 테스트 제출 요청"""

    answers: List[SurveyAnswerDto]

    model_config = {"populate_by_name": True}
