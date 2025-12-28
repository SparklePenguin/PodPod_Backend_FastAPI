from fastapi import APIRouter, Depends, Query

from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.service import get_artist_suggestion_service
from app.features.artists.schemas import (
    ArtistSuggestionCreateRequest,
    ArtistSuggestionDto,
    ArtistSuggestionRankingDto,
)
from app.features.artists.services.artist_suggestion_service import (
    ArtistSuggestionService,
)

router = APIRouter(tags=["artist-suggestions"])


@router.post(
    "",
    response_model=BaseResponse[ArtistSuggestionDto],
    description="아티스트 제안 생성",
)
async def create_artist_suggestion(
    request: ArtistSuggestionCreateRequest,
    user_id: int = Depends(get_current_user_id),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 제안 생성"""
    result = await service.create_suggestion(request, user_id)
    return BaseResponse.ok(
        data=result,
        http_status=201,
        message_ko="아티스트 제안이 성공적으로 생성되었습니다.",
    )


@router.get(
    "/ranking",
    response_model=BaseResponse[PageDto[ArtistSuggestionRankingDto]],
    description="아티스트 요청 순위 조회",
)
async def get_artist_ranking(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    service: ArtistSuggestionService = Depends(get_artist_suggestion_service),
):
    """아티스트 요청 순위 조회"""
    result = await service.get_artist_ranking(page, size)
    return BaseResponse.ok(data=result, message_ko="아티스트 요청 순위를 조회했습니다.")
