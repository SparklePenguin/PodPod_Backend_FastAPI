from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.services.artist_service import ArtistService
from app.schemas.artist import ArtistDto
from app.schemas.common import SuccessResponse, ErrorResponse

router = APIRouter()


def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)


# - MARK: 공개 API
@router.get(
    "/",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "아티스트 목록 조회 성공"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    summary="아티스트 목록 조회",
    description="모든 아티스트 목록을 조회합니다.",
)
async def get_artists(
    artist_service: ArtistService = Depends(get_artist_service),
):
    """아티스트 목록 조회"""
    try:
        artists = await artist_service.get_artists()
        return SuccessResponse(
            code=200,
            message="artists_retrieved_successfully",
            data={"artists": artists},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="artists_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


@router.get(
    "/{artist_id}",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "아티스트 조회 성공"},
        404: {"model": ErrorResponse, "description": "아티스트를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    summary="특정 아티스트 조회",
    description="특정 아티스트의 정보를 조회합니다.",
)
async def get_artist(
    artist_id: int,
    artist_service: ArtistService = Depends(get_artist_service),
):
    """특정 아티스트 조회"""
    try:
        artist = await artist_service.get_artist(artist_id)
        if not artist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="artist_not_found",
                    status=status.HTTP_404_NOT_FOUND,
                    message="아티스트를 찾을 수 없습니다.",
                ).model_dump(),
            )
        return SuccessResponse(
            code=200, message="artist_retrieved_successfully", data={"artist": artist}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="artist_retrieval_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )


# - MARK: 내부용 API
@router.post(
    "/mvp",
    response_model=SuccessResponse,
    responses={
        200: {"model": SuccessResponse, "description": "MVP 아티스트 생성 성공"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
    tags=["internal"],
    summary="MVP 아티스트 생성 (내부용)",
    description="⚠️ 내부용 API - MVP 아티스트들을 생성합니다. 개발/테스트 목적으로만 사용됩니다.",
)
async def create_mvp_artists(
    artist_service: ArtistService = Depends(get_artist_service),
):
    """MVP 아티스트들 생성 (내부용)"""
    try:
        artists = await artist_service.create_mvp_artists()
        return SuccessResponse(
            code=200,
            message="mvp_artists_created_successfully",
            data={"artists": artists},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="mvp_artists_creation_failed",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e),
            ).model_dump(),
        )
