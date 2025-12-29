"""Artists feature models"""

# 공통 모델은 shared에서 import
from shared.models.artist import Artist
from shared.models.artist_image import ArtistImage
from shared.models.artist_name import ArtistName
from shared.models.artist_unit import ArtistUnit

# 도메인 특화 모델
from .artist_schedule import ArtistSchedule
from .artist_suggestion import ArtistSuggestion
from .schedule_content import ScheduleContent
from .schedule_member import ScheduleMember
from .schedule_type import ScheduleType

__all__ = [
    # 아티스트 기본 모델 (shared)
    "Artist",
    "ArtistImage",
    "ArtistName",
    "ArtistUnit",
    # 아티스트 스케줄 모델
    "ArtistSchedule",
    "ScheduleMember",
    "ScheduleContent",
    "ScheduleType",
    # 아티스트 제안 모델
    "ArtistSuggestion",
]
