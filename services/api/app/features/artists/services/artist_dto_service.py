"""Artist DTO Service - 모델을 DTO로 변환하는 서비스"""

from app.features.artists.schemas import (
    ArtistDto,
    ArtistScheduleDto,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)


class ArtistDtoService:
    """Artist 관련 모델 → DTO 변환 전담 서비스"""

    # - MARK: Artist DTO 변환
    @staticmethod
    def to_artist_dto(artist) -> ArtistDto:
        """단일 Artist 모델을 DTO로 변환"""
        return ArtistDto.model_validate(artist, from_attributes=True)

    @staticmethod
    def to_artist_dtos(artists: list) -> list[ArtistDto]:
        """Artist 모델 리스트를 DTO 리스트로 변환"""
        return [
            ArtistDto.model_validate(artist, from_attributes=True) for artist in artists
        ]

    # - MARK: ArtistSchedule DTO 변환
    @staticmethod
    def to_schedule_dto(schedule) -> ArtistScheduleDto:
        """단일 ArtistSchedule 모델을 DTO로 변환"""
        return ArtistScheduleDto.model_validate(schedule, from_attributes=True)

    @staticmethod
    def to_schedule_dtos(schedules: list) -> list[ArtistScheduleDto]:
        """ArtistSchedule 모델 리스트를 DTO 리스트로 변환"""
        return [
            ArtistScheduleDto.model_validate(schedule, from_attributes=True)
            for schedule in schedules
        ]

    # - MARK: ArtistSuggestion DTO 변환
    @staticmethod
    def to_suggestion_dto(suggestion) -> ArtistSuggestionDto:
        """단일 ArtistSuggestion 모델을 DTO로 변환"""
        return ArtistSuggestionDto.model_validate(suggestion)

    @staticmethod
    def to_suggestion_dtos(suggestions: list) -> list[ArtistSuggestionDto]:
        """ArtistSuggestion 모델 리스트를 DTO 리스트로 변환"""
        return [
            ArtistSuggestionDto.model_validate(suggestion) for suggestion in suggestions
        ]

    # - MARK: ArtistSuggestionRanking DTO 변환
    @staticmethod
    def to_ranking_dtos(rankings: list[dict]) -> list[ArtistSuggestionRankingDto]:
        """랭킹 데이터를 DTO 리스트로 변환"""
        return [
            ArtistSuggestionRankingDto(
                artist_name=ranking["artist_name"], count=ranking["count"]
            )
            for ranking in rankings
        ]
