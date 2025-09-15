from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.artist_service import ArtistService
from app.schemas.common import BaseResponse, PageDto
from app.schemas.artist import ArtistDto
from app.schemas.artist_image import (
    ArtistImageDto,
    UpdateArtistImageRequest,
    BulkUpdateArtistImagesRequest,
)
from app.crud.artist import ArtistCRUD
from app.core.http_status import HttpStatus

router = APIRouter()


def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)


# - MARK: 아티스트 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[PageDto[ArtistDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistDto]],
            "description": "아티스트 목록 조회 성공",
        },
    },
    summary="아티스트 목록 조회",
    description="아티스트 목록을 페이지네이션과 필터링으로 조회합니다. 기본적으로 활성화된 아티스트만 반환합니다.",
)
async def get_artists(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    is_active: bool = Query(True, description="활성화 상태 필터 (true/false)"),
    artist_service: ArtistService = Depends(get_artist_service),
):
    """아티스트 목록 조회 (페이지네이션 및 is_active 필터링 지원)"""
    page_data = await artist_service.get_artists(
        page=page, page_size=page_size, is_active=is_active
    )
    return BaseResponse.ok(data=page_data)


# - MARK: 특정 아티스트 조회
@router.get(
    "/{artist_id}",
    response_model=BaseResponse[PageDto[ArtistDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistDto]],
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
    if not artist:
        return BaseResponse.error(code=HttpStatus.NOT_FOUND, message="artist_not_found")
    return BaseResponse.ok(data=artist)


# - MARK: MVP 아티스트 생성 (내부용)
@router.post(
    "/mvp",
    response_model=BaseResponse[dict],
    responses={
        200: {"model": BaseResponse[dict], "description": "BLIP+MVP 동기화 성공"},
    },
    tags=["internal"],
    summary="MVP 아티스트 생성 (내부용)",
    description="⚠️ 내부용 API - BLIP 전체 데이터와 MVP 목록을 병합하여 동기화합니다.",
)
async def sync_mvp_artists(
    artist_service: ArtistService = Depends(get_artist_service),
):
    """BLIP+MVP 병합 동기화 (내부용)"""
    result = await artist_service.sync_blip_and_mvp()
    return BaseResponse.ok(data=result)


# - MARK: 아티스트 이미지 관리 (내부용)
@router.put(
    "/{artist_id}/images",
    response_model=BaseResponse[Dict[str, Any]],
    tags=["internal"],
    summary="아티스트 이미지 일괄 업데이트",
    description="⚠️ 내부용 API - 특정 아티스트의 모든 이미지를 일괄 업데이트합니다.",
)
async def bulk_update_artist_images(
    artist_id: int = Path(..., description="아티스트 ID"),
    request: BulkUpdateArtistImagesRequest = ...,
    db: AsyncSession = Depends(get_db),
):
    """아티스트의 모든 이미지를 일괄 업데이트합니다."""
    try:
        artist_crud = ArtistCRUD(db)

        # 이미지 데이터를 딕셔너리 형태로 변환
        images_data = [image.model_dump() for image in request.images]

        success, message = await artist_crud.update_artist_images(
            artist_id, images_data
        )

        if not success:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=message,
            )

        return BaseResponse.ok(
            data={
                "message": message,
                "artist_id": artist_id,
                "updated_count": len(images_data),
            },
            http_status=HttpStatus.OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"아티스트 이미지 업데이트 실패: {str(e)}",
        )


@router.get(
    "/{artist_id}/images",
    response_model=BaseResponse[list[ArtistImageDto]],
    tags=["internal"],
    summary="아티스트 이미지 목록 조회",
    description="⚠️ 내부용 API - 특정 아티스트의 모든 이미지를 조회합니다.",
)
async def get_artist_images(
    artist_id: int = Path(..., description="아티스트 ID"),
    db: AsyncSession = Depends(get_db),
):
    """아티스트의 모든 이미지를 조회합니다."""
    try:
        artist_crud = ArtistCRUD(db)

        # 아티스트 조회 (이미지 포함)
        artist = await artist_crud.get_by_id(artist_id)

        if not artist:
            raise HTTPException(
                status_code=HttpStatus.NOT_FOUND,
                detail=f"아티스트를 찾을 수 없습니다. ID: {artist_id}",
            )

        # 이미지 데이터를 DTO로 변환
        images = [ArtistImageDto.model_validate(image) for image in artist.images]

        return BaseResponse.ok(
            data=images,
            http_status=HttpStatus.OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"아티스트 이미지 조회 실패: {str(e)}",
        )


@router.put(
    "/artist-images/{image_id}",
    response_model=BaseResponse[Dict[str, Any]],
    tags=["internal"],
    summary="단일 아티스트 이미지 업데이트",
    description="⚠️ 내부용 API - 특정 아티스트 이미지를 업데이트합니다.",
)
async def update_single_artist_image(
    image_id: int = Path(..., description="이미지 ID"),
    request: UpdateArtistImageRequest = ...,
    db: AsyncSession = Depends(get_db),
):
    """단일 아티스트 이미지를 업데이트합니다."""
    try:
        artist_crud = ArtistCRUD(db)

        # 요청 데이터를 딕셔너리로 변환 (None 값 제외)
        image_data = {k: v for k, v in request.model_dump().items() if v is not None}

        if not image_data:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="업데이트할 데이터가 없습니다.",
            )

        success, message = await artist_crud.update_single_artist_image(
            image_id, image_data
        )

        if not success:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail=message,
            )

        return BaseResponse.ok(
            data={"message": message, "image_id": image_id},
            http_status=HttpStatus.OK,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_SERVER_ERROR,
            detail=f"아티스트 이미지 업데이트 실패: {str(e)}",
        )
