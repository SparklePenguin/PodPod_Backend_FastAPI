from typing import List
from pydantic import BaseModel, Field


class LocationDto(BaseModel):
    """지역 정보 DTO"""

    id: int = Field(description="지역 ID")
    main_location: str = Field(alias="mainLocation", description="주요 지역")
    sub_locations: List[str] = Field(
        alias="subLocations", description="세부 지역 리스트"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class LocationResponse(BaseModel):
    """지역 응답 DTO"""

    main_location: str = Field(alias="mainLocation", description="주요 지역")
    sub_locations: List[str] = Field(
        alias="subLocations", description="세부 지역 리스트"
    )

    model_config = {
        "populate_by_name": True,
    }
