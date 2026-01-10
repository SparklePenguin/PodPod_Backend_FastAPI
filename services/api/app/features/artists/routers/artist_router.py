from app.common.schemas import BaseResponse, PageDto
from app.deps.providers import get_artist_use_case, get_artists_use_case
from app.features.artists.schemas import ArtistDto
from app.features.artists.use_cases.artist_use_cases import (
    GetArtistsUseCase,
    GetArtistUseCase,
)
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/artists", tags=["artists"])


# - MARK: 아티스트 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[PageDto[ArtistDto]],
    description="아티스트 목록 조회",
)
async def get_artists(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    is_active: bool = Query(True, description="활성화 상태 필터 (true/false)"),
    use_case: GetArtistsUseCase = Depends(get_artists_use_case),
):
    result = await use_case.execute(page, size, is_active)
    return BaseResponse.ok(data=result)


# - MARK: 아티스트 조회
@router.get(
    "/{artist_id}", response_model=BaseResponse[ArtistDto], description="아티스트 조회"
)
async def get_artist(
    artist_id: int,
    use_case: GetArtistUseCase = Depends(get_artist_use_case),
):
    result = await use_case.execute(artist_id)
    return BaseResponse.ok(data=result)
