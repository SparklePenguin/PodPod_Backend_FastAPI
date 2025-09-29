from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.services.artist_suggestion_service import ArtistSuggestionService
from app.schemas.artist_suggestion import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionNameOnlyRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)
from app.schemas.common import BaseResponse, PageDto
from app.core.http_status import HttpStatus

router = APIRouter()


def get_artist_suggestion_service(
    db: AsyncSession = Depends(get_db),
) -> ArtistSuggestionService:
    return ArtistSuggestionService(db)


# - MARK: 아티스트 제안 생성 (상세 정보 포함)
@router.post(
    "/",
    response_model=BaseResponse[ArtistSuggestionDto],
    responses={
        HttpStatus.CREATED: {
            "model": BaseResponse[ArtistSuggestionDto],
            "description": "아티스트 제안 생성 성공",
        },
    },
)
async def create_artist_suggestion(
    request: ArtistSuggestionCreateRequest,
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 제안 생성 (아티스트명, 추천 이유, 이메일)"""
    suggestion = await service.create_suggestion(request)
    return BaseResponse.created(
        data=suggestion, message_ko="아티스트 제안이 성공적으로 생성되었습니다."
    )


# - MARK: 아티스트 제안 생성 (이름만)
@router.post(
    "/name-only",
    response_model=BaseResponse[ArtistSuggestionDto],
    responses={
        HttpStatus.CREATED: {
            "model": BaseResponse[ArtistSuggestionDto],
            "description": "아티스트 제안 생성 성공 (이름만)",
        },
    },
)
async def create_artist_suggestion_name_only(
    request: ArtistSuggestionNameOnlyRequest,
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 제안 생성 (아티스트명만)"""
    suggestion = await service.create_suggestion_name_only(request)
    return BaseResponse.created(
        data=suggestion, message_ko="아티스트 제안이 성공적으로 생성되었습니다."
    )


# - MARK: 아티스트별 요청 순위 조회
@router.get(
    "/ranking",
    response_model=BaseResponse[List[ArtistSuggestionRankingDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[List[ArtistSuggestionRankingDto]],
            "description": "아티스트 요청 순위 조회 성공",
        },
    },
)
async def get_artist_ranking(
    limit: Optional[int] = Query(
        default=50, ge=1, le=100, description="조회할 순위 개수"
    ),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트별 요청 순위 조회 (가장 많이 요청된 순)"""
    if limit is None:
        limit = 50
    rankings = await service.get_artist_ranking(limit)
    return BaseResponse.ok(
        data=rankings, message_ko="아티스트 요청 순위를 조회했습니다."
    )


# - MARK: 제안 조회 (ID로)
@router.get(
    "/{suggestion_id}",
    response_model=BaseResponse[ArtistSuggestionDto],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[ArtistSuggestionDto],
            "description": "제안 조회 성공",
        },
        HttpStatus.NOT_FOUND: {
            "model": BaseResponse[None],
            "description": "제안을 찾을 수 없습니다",
        },
    },
)
async def get_suggestion(
    suggestion_id: int = Path(..., description="제안 ID"),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """ID로 아티스트 제안 조회"""
    suggestion = await service.get_suggestion_by_id(suggestion_id)
    if not suggestion:
        return BaseResponse.not_found(message_ko="제안을 찾을 수 없습니다.")

    return BaseResponse.ok(data=suggestion, message_ko="제안을 조회했습니다.")


# - MARK: 제안 목록 조회
@router.get(
    "/",
    response_model=BaseResponse[PageDto[ArtistSuggestionDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistSuggestionDto]],
            "description": "제안 목록 조회 성공",
        },
    },
)
async def get_suggestions(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 제안 목록 조회"""
    suggestions = await service.get_suggestions(page, size)
    return BaseResponse.ok(data=suggestions, message_ko="제안 목록을 조회했습니다.")


# - MARK: 특정 아티스트 제안 목록 조회
@router.get(
    "/artist/{artist_name}",
    response_model=BaseResponse[PageDto[ArtistSuggestionDto]],
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistSuggestionDto]],
            "description": "특정 아티스트 제안 목록 조회 성공",
        },
    },
)
async def get_suggestions_by_artist_name(
    artist_name: str = Path(..., description="아티스트명"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """특정 아티스트명으로 제안 목록 조회"""
    suggestions = await service.get_suggestions_by_artist_name(artist_name, page, size)
    return BaseResponse.ok(
        data=suggestions,
        message_ko=f"'{artist_name}' 아티스트 제안 목록을 조회했습니다.",
    )
