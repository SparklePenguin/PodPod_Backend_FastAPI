from fastapi import APIRouter, Depends, Query

from app.common.schemas import BaseResponse, PageDto
from app.core.http_status import HttpStatus
from app.deps.service import get_artist_service
from app.features.artists.schemas.artist_schemas import ArtistDto, ArtistSimpleDto
from app.features.artists.services.artist_service import ArtistService

router = APIRouter()


# - MARK: 아티스트 목록 조회 (간소화)
@router.get(
    "/simple",
    response_model=BaseResponse[PageDto[ArtistSimpleDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistSimpleDto]],
            "description": "아티스트 목록 조회 성공 (간소화)",
        },
    },
    summary="아티스트 목록 조회 (간소화)",
    description="아티스트 목록을 간소화된 형태로 조회합니다. ArtistUnit의 artist_id에 해당하는 아티스트 정보(unitId, artistId, 이름)를 반환합니다.",
)
async def get_artists_simple(
    page: int = Query(
        1, ge=1, serialization_alias="page", description="페이지 번호 (1부터 시작)"
    ),
    size: int = Query(
        20, ge=1, le=100, serialization_alias="size", description="페이지 크기 (1~100)"
    ),
    is_active: bool = Query(
        True,
        serialization_alias="isActive",
        description="활성화 상태 필터 (true/false)",
    ),
    artist_service: ArtistService = Depends(get_artist_service),
):
    """아티스트 목록 조회 (간소화 - ArtistUnit의 artist_id에 해당하는 아티스트 정보)"""
    page_data = await artist_service.get_artists_simple(
        page=page, size=size, is_active=is_active
    )
    return BaseResponse.ok(data=page_data)


# - MARK: 아티스트 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[PageDto[ArtistDto]],
)
async def get_artists(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    is_active: bool = Query(True, description="활성화 상태 필터 (true/false)"),
    artist_service: ArtistService = Depends(get_artist_service),
):
    """아티스트 목록 조회 (페이지네이션 및 is_active 필터링 지원)"""
    page_data = await artist_service.get_artists(
        page=page, size=size, is_active=is_active
    )
    return BaseResponse.ok(data=page_data)


# - MARK: 특정 아티스트 조회
@router.get(
    "/{artist_id}",
    response_model=BaseResponse[ArtistDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[ArtistDto],
            "description": "아티스트 조회 성공",
        },
    },
    summary="특정 아티스트 조회",
    description="ID로 특정 아티스트의 상세 정보를 조회합니다. 이미지, 멤버, 다국어 이름 등 모든 관련 데이터를 포함합니다.",
)
async def get_artist(
    artist_id: int,
    artist_service: ArtistService = Depends(get_artist_service),
):
    """특정 아티스트 조회"""
    artist = await artist_service.get_artist(artist_id)
    return BaseResponse.ok(data=artist)
