from typing import List

from pydantic import BaseModel

from .survey_answer_dto import SurveyAnswerDto


class SubmitTendencyTestRequest(BaseModel):
    """성향 테스트 제출 요청"""

    answers: List[SurveyAnswerDto]

    model_config = {"populate_by_name": True}
