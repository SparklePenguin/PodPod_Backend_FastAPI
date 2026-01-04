"""Artists feature models"""

# 공통 모델은 shared에서 import
from shared.models.artist import Artist
from shared.models.artist_image import ArtistImage
from shared.models.artist_name import ArtistName
from shared.models.artist_unit import ArtistUnit

# 도메인 특화 모델
from .schedule_models import (
    ArtistSchedule,
    ScheduleContent,
    ScheduleMember,
    ScheduleType,
)
from .suggestion_models import (
    ArtistSuggestion,
)

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
