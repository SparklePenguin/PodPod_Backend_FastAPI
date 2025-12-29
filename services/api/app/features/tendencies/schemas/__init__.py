"""Tendencies feature schemas"""

from .submit_tendency_test_request import SubmitTendencyTestRequest
from .survey_answer_dto import SurveyAnswerDto
from .tendency_dto import TendencyDto
from .tendency_info_dto import TendencyInfoDto
from .tendency_result_dto import TendencyResultDto
from .tendency_survey_dto import TendencySurveyDto
from .user_tendency_result_dto import UserTendencyResultDto

__all__ = [
    "SurveyAnswerDto",
    "SubmitTendencyTestRequest",
    "TendencyDto",
    "TendencyInfoDto",
    "TendencyResultDto",
    "TendencySurveyDto",
    "UserTendencyResultDto",
]
