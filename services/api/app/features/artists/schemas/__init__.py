"""Artists feature schemas"""

from .artist_detail_dto import ArtistDetailDto, ArtistDto, ArtistSimpleDto
from .artist_image import ArtistImageDto, UpdateArtistImageRequest
from .artist_name import ArtistNameDto
from .artist_schedule import (
    ArtistScheduleCreateRequest,
    ArtistScheduleDto,
    ScheduleContentCreateRequest,
    ScheduleContentDto,
    ScheduleMemberCreateRequest,
    ScheduleMemberDto,
    ScheduleTypeEnum,
)
from .artist_suggestion import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)
from .artist_sync_dto import ArtistsSyncDto
from .artist_unit import ArtistUnitDto

__all__ = [
    # 아티스트 기본
    "ArtistDto",
    "ArtistDetailDto",
    "ArtistSimpleDto",
    "ArtistImageDto",
    "ArtistNameDto",
    "ArtistUnitDto",
    "ArtistsSyncDto",
    "UpdateArtistImageRequest",
    # 아티스트 스케줄
    "ArtistScheduleDto",
    "ArtistScheduleCreateRequest",
    "ScheduleMemberDto",
    "ScheduleMemberCreateRequest",
    "ScheduleContentDto",
    "ScheduleContentCreateRequest",
    "ScheduleTypeEnum",
    # 아티스트 제안
    "ArtistSuggestionDto",
    "ArtistSuggestionCreateRequest",
    "ArtistSuggestionRankingDto",
]
