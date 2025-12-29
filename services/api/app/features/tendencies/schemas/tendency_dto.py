from pydantic import BaseModel, Field

from .tendency_info_dto import TendencyInfoDto


class TendencyDto(BaseModel):
    """성향 테스트 결과 응답"""

    type: str
    description: str
    tendency_info: TendencyInfoDto = Field(..., alias="tendencyInfo")

    model_config = {"populate_by_name": True}
