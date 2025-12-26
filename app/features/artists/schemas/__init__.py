"""Artists feature schemas"""

from .artist_schedule_schemas import (
    ArtistScheduleCreateRequest,
    ArtistScheduleDto,
    ScheduleContentCreateRequest,
    ScheduleContentDto,
    ScheduleMemberCreateRequest,
    ScheduleMemberDto,
    ScheduleTypeEnum,
)
from .artist_schemas import (
    ArtistDto,
    ArtistImageDto,
    ArtistNameDto,
    ArtistSimpleDto,
    ArtistsSyncDto,
    ArtistUnitDto,
    UpdateArtistImageRequest,
)
from .artist_suggestion_schemas import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)

__all__ = [
    # 아티스트 기본
    "ArtistDto",
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
