from app.features.follow.repositories.follow_list_repository import FollowListRepository
from app.features.follow.services.follow_utils import (
    create_page_dto,
    create_simple_user_dto,
)
from sqlalchemy.ext.asyncio import AsyncSession


class FollowListService:
    """팔로우 목록 조회 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._follow_list_repo = FollowListRepository(session)

    # - MARK: 팔로우하는 사용자 목록 조회
    async def get_following_list(self, user_id: int, page: int = 1, size: int = 20):
        """팔로우하는 사용자 목록 조회"""

        following_data, total_count = await self._follow_list_repo.get_following_list(
            user_id, page, size
        )

        users = []
        for user, created_at, tendency_type in following_data:
            try:
                user_dto = create_simple_user_dto(
                    user, tendency_type=tendency_type, is_following=True
                )
                users.append(user_dto)
            except ValueError:
                continue  # 유효하지 않은 사용자는 건너뛰기

        return create_page_dto(users, page, size, total_count)

    # - MARK: 팔로워 목록 조회
    async def get_followers_list(
        self,
        user_id: int,
        current_user_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ):
        """팔로워 목록 조회"""

        followers_data, total_count = await self._follow_list_repo.get_followers_list(
            user_id, page, size
        )

        # N+1 문제 해결: 현재 사용자가 팔로우하는 사용자 ID 목록을 한 번에 조회
        following_user_ids = await self._get_following_user_ids(
            current_user_id, followers_data
        )

        users = []
        for user, created_at, tendency_type in followers_data:
            try:
                follower_user_id = user.id
                is_following = (
                    follower_user_id in following_user_ids
                    if current_user_id and follower_user_id
                    else False
                )
                user_dto = create_simple_user_dto(
                    user, tendency_type=tendency_type, is_following=is_following
                )
                users.append(user_dto)
            except ValueError:
                continue  # 유효하지 않은 사용자는 건너뛰기

        return create_page_dto(users, page, size, total_count)

    # - MARK: 현재 사용자가 팔로우하는 사용자 ID 목록 조회 (재사용 가능)
    async def _get_following_user_ids(
        self, current_user_id: int | None, users_data: list
    ) -> set[int]:
        """현재 사용자가 팔로우하는 사용자 ID 목록을 한 번에 조회"""
        if not current_user_id:
            return set()

        # 사용자 ID 목록 추출
        user_ids = [user.id for user, _, _ in users_data if user.id]
        if not user_ids:
            return set()

        # 한 번의 쿼리로 현재 사용자가 팔로우하는 사용자 ID 목록 조회
        following_ids = await self._follow_list_repo.get_following_ids_by_user_ids(
            current_user_id, user_ids
        )
        return set(following_ids)

    # - MARK: 추천 유저 목록 조회
    async def get_recommended_users(self, user_id: int, page: int = 1, size: int = 20):
        """추천 유저 목록 조회 (현재는 랜덤 유저 반환)"""

        recommended_users = await self._follow_list_repo.get_recommended_users(
            user_id, page, size
        )

        users = []
        for user, tendency_type in recommended_users:
            try:
                user_dto = create_simple_user_dto(
                    user, tendency_type=tendency_type, is_following=False
                )
                users.append(user_dto)
            except ValueError:
                continue  # 유효하지 않은 사용자는 건너뛰기

        # 추천 유저는 총 개수를 정확히 알 수 없으므로 간단하게 처리
        total_count = len(users)
        return create_page_dto(users, page, size, total_count)
