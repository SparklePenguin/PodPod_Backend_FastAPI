from typing import List
from pydantic import BaseModel, Field

from .artist import ArtistDto
from .common import SuccessResponse, PageDto


# - MARK: 아티스트 목록 응답
class ArtistsListResponse(SuccessResponse):
    data: PageDto[ArtistDto] = Field(
        alias="data",
        example=PageDto(
            items=[],
            current_page=1,
            page_size=20,
            total_count=0,
            total_pages=0,
            has_next=False,
            has_prev=False,
        ),
    )


# - MARK: 아티스트 상세 데이터
class ArtistDetailData(BaseModel):
    artist: ArtistDto = Field(
        alias="artist",
        example=ArtistDto(
            id=0,
            name="string",
            unit_id=0,
            blip_artist_id=0,
            images=[],
            names=[],
        ),
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ArtistDetailResponse(SuccessResponse):
    data: ArtistDetailData


# - MARK: 동기화 응답
class ArtistsSyncData(BaseModel):
    artist_created: int = Field(alias="artist_created", example=0)
    artist_updated: int = Field(alias="artist_updated", example=0)
    unit_created: int = Field(alias="unit_created", example=0)
    unit_updated: int = Field(alias="unit_updated", example=0)
    left_mvp_names: List[str] = Field(alias="left_mvp_names", example=[])

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ArtistsSyncResponse(SuccessResponse):
    data: ArtistsSyncData
