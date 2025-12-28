"""Artists feature schemas"""

from .artist_detail_dto import ArtistDetailDto
from .artist_dto import ArtistDto
from .artist_image_dto import ArtistImageDto
from .artist_name_dto import ArtistNameDto
from .artist_schedule_create_request import ArtistScheduleCreateRequest
from .artist_schedule_dto import ArtistScheduleDto
from .artist_simple_dto import ArtistSimpleDto
from .artist_suggestion_create_request import ArtistSuggestionCreateRequest
from .artist_suggestion_dto import ArtistSuggestionDto
from .artist_suggestion_ranking_dto import ArtistSuggestionRankingDto
from .artists_sync_dto import ArtistsSyncDto
from .artist_unit_dto import ArtistUnitDto
from .schedule_content_create_request import ScheduleContentCreateRequest
from .schedule_content_dto import ScheduleContentDto
from .schedule_member_create_request import ScheduleMemberCreateRequest
from .schedule_member_dto import ScheduleMemberDto
from .schedule_type_enum import ScheduleTypeEnum
from .update_artist_image_request import UpdateArtistImageRequest

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
