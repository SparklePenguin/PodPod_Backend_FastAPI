from fastapi import APIRouter, Depends, Query

from app.common.schemas import BaseResponse, PageDto
from app.deps.service import get_artist_service
from app.features.artists.schemas import ArtistDto
from app.features.artists.services.artist_service import ArtistService

router = APIRouter()


# MARK: - 아티스트 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[PageDto[ArtistDto]],
    description="아티스트 목록 조회",
)
async def get_artists(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    is_active: bool = Query(True, description="활성화 상태 필터 (true/false)"),
    service: ArtistService = Depends(get_artist_service),
):
    result = await service.get_artists(page, size, is_active)
    return BaseResponse.ok(result)


# MARK: - 아티스트 조회
@router.get(
    "/{artist_id}",
    response_model=BaseResponse[ArtistDto],
    description="아티스트 조회",
)
async def get_artist(
    artist_id: int,
    service: ArtistService = Depends(get_artist_service),
):
    result = await service.get_artist(artist_id)
    return BaseResponse.ok(result)
