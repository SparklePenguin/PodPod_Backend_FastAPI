from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


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
