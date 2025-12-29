from pydantic import BaseModel, Field


class SurveyAnswerDto(BaseModel):
    """성향 테스트 답변 스키마"""

    question_id: int = Field(..., alias="questionId")
    id: int = Field(...)

    model_config = {"populate_by_name": True}
