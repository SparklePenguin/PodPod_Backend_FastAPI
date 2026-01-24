from typing import List

from fastapi import (
    Depends, )

from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.providers import (
    get_user_artist_use_case,
)
from app.features.artists.schemas import ArtistDto
from app.features.users.routers import (

    UserPreferredArtistsController,
)
from app.features.users.schemas import (
    UpdatePreferredArtistsRequest,
)
from app.features.users.use_cases.user_artist_use_case import UserArtistUseCase


class UserPreferredArtistsRouter:

    @staticmethod
    @UserPreferredArtistsController.ROUTER.get(
        path=UserPreferredArtistsController.PREFIX,
        summary="선호 아티스트 조회",
        response_model=BaseResponse[List[ArtistDto]],
        description="사용자 선호 아티스트 조회 (토큰 필요)",
    )
    async def get_user_preferred_artists(
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserArtistUseCase = Depends(get_user_artist_use_case),
    ):
        artists = await use_case.get_preferred_artists(current_user_id)
        return BaseResponse.ok(data=artists)

    @staticmethod
    @UserPreferredArtistsController.ROUTER.put(
        path=UserPreferredArtistsController.PREFIX,
        summary="선호 아티스트 업데이트",
        response_model=BaseResponse[dict],
        description="현재 사용자의 선호 아티스트 목록을 업데이트합니다.",
    )
    async def update_user_preferred_artists(
            artists_data: UpdatePreferredArtistsRequest,
            current_user_id: int = Depends(get_current_user_id),
            use_case: UserArtistUseCase = Depends(get_user_artist_use_case),
    ):
        artists = await use_case.update_preferred_artists(
            current_user_id, artists_data.artist_ids
        )
        return BaseResponse.ok(data={"artists": artists})
