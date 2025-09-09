from typing import List

from app.schemas.schedule import (
    ArtistScheduleDto,
    ArtistScheduleContnetDto,
)


class ArtistScheduleService:
    @staticmethod
    def get_sample_schedule(artist_id: int) -> ArtistScheduleDto:
        return ArtistScheduleDto(
            artistId=artist_id,
            scheduleType=2,
            scheduleStartTime="2025-02-02T15:00:00Z",
            scheduleEndTime="2025-02-02T15:00:00Z",
            scheduleText="Hearts2Hearts 하츠투하츠 'Chase Your Choice' Debut Trailer",
            scheduleTitle="<'Chase Your Choice' Debut Trailer>",
            scheduleMembers=[],
            scheduleContents=[
                ArtistScheduleContnetDto(
                    scheduleContentType="video",
                    scheduleContentPath="https://youtu.be/srEUps3-5mo",
                    scheduleContentTitle=None,
                )
            ],
            scheduleChannel=None,
            scheduleLocation=None,
        )
