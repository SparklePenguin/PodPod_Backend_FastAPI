from typing import List

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
