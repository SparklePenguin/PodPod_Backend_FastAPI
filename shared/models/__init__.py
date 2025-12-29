"""
공유 모델 모듈
메인 API와 스크래핑 서비스에서 공통으로 사용하는 SQLAlchemy 모델들
"""

from shared.models.artist import Artist
from shared.models.artist_image import ArtistImage
from shared.models.artist_name import ArtistName
from shared.models.artist_unit import ArtistUnit

__all__ = [
    "Artist",
    "ArtistImage",
    "ArtistName",
    "ArtistUnit",
]
