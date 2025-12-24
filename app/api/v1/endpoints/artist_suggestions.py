from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.common.schemas import BaseResponse, PageDto
from app.core.database import get_db
from app.core.http_status import HttpStatus
from app.features.artists.schemas.artist_suggestion_schemas import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)
from app.features.artists.services.suggestion_service import ArtistSuggestionService

router = APIRouter(tags=["artist-suggestions"])


def get_artist_suggestion_service(
    db: AsyncSession = Depends(get_db),
) -> ArtistSuggestionService:
    return ArtistSuggestionService(db)


# - MARK: 아티스트 제안 생성 (상세 정보 포함)
@router.post(
    "",
    response_model=BaseResponse[ArtistSuggestionDto],
    summary="아티스트 제안 생성",
    description="아티스트명, 추천 이유, 이메일을 포함한 상세한 아티스트 제안을 생성합니다.",
    responses={
        HttpStatus.CREATED: {
            "model": BaseResponse[ArtistSuggestionDto],
            "description": "아티스트 제안 생성 성공",
        },
        HttpStatus.CONFLICT: {
            "model": BaseResponse[None],
            "description": "이미 해당 아티스트에 대한 제안을 하셨습니다",
        },
    },
)
async def create_artist_suggestion(
    request: ArtistSuggestionCreateRequest,
    user_id: int = Depends(get_current_user_id),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 제안 생성"""
    suggestion = await service.create_suggestion(request, user_id)
    return BaseResponse.created(
        data=suggestion, message_ko="아티스트 제안이 성공적으로 생성되었습니다."
    )


# - MARK: 아티스트별 요청 순위 조회
@router.get(
    "/ranking",
    response_model=BaseResponse[PageDto[ArtistSuggestionRankingDto]],
    summary="아티스트 요청 순위 조회",
    description="가장 많이 요청된 아티스트들의 순위를 페이지네이션으로 조회합니다.",
    responses={
        HttpStatus.OK: {
            "model": BaseResponse[PageDto[ArtistSuggestionRankingDto]],
            "description": "아티스트 요청 순위 조회 성공",
        },
    },
)
async def get_artist_ranking(
    page: int = Query(
        1, ge=1, serialization_alias="page", description="페이지 번호 (1부터 시작)"
    ),
    size: int = Query(
        20, ge=1, le=100, serialization_alias="size", description="페이지 크기 (1~100)"
    ),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 요청 순위 조회"""
    rankings = await service.get_artist_ranking(page, size)
    return BaseResponse.ok(
        data=rankings, message_ko="아티스트 요청 순위를 조회했습니다."
    )
