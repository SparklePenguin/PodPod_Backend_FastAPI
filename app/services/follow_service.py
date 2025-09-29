from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from app.crud.follow import FollowCRUD
from app.crud.pod.pod import PodCRUD
from app.schemas.follow import (
    FollowRequest,
    FollowResponse,
    UserFollowDto,
    FollowListResponse,
    FollowStatsResponse,
)
from app.schemas.pod.pod_dto import PodDto
from app.schemas.common.page_dto import PageDto
from app.core.error_codes import get_error_info


class FollowService:
    """팔로우 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = FollowCRUD(db)
        self.pod_crud = PodCRUD(db)

    async def follow_user(self, follower_id: int, following_id: int) -> FollowResponse:
        """사용자 팔로우"""
        follow = await self.crud.create_follow(follower_id, following_id)

        if not follow:
            raise ValueError("팔로우에 실패했습니다.")

        return FollowResponse.model_validate(follow)

    async def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """사용자 팔로우 취소"""
        return await self.crud.delete_follow(follower_id, following_id)

    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserFollowDto]:
        """팔로우하는 사용자 목록 조회"""
        following_data, total_count = await self.crud.get_following_list(
            user_id, page, size
        )

        users = []
        for user, created_at, tendency_type in following_data:
            user_dto = UserFollowDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                tendency_type=tendency_type,
                created_at=created_at,
            )
            users.append(user_dto)

        has_next = (page * size) < total_count

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=users,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_followers_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserFollowDto]:
        """팔로워 목록 조회"""
        followers_data, total_count = await self.crud.get_followers_list(
            user_id, page, size
        )

        users = []
        for user, created_at, tendency_type in followers_data:
            user_dto = UserFollowDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                tendency_type=tendency_type,
                created_at=created_at,
            )
            users.append(user_dto)

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=users,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_follow_stats(
        self, user_id: int, current_user_id: Optional[int] = None
    ) -> FollowStatsResponse:
        """팔로우 통계 조회"""
        stats = await self.crud.get_follow_stats(user_id, current_user_id)

        return FollowStatsResponse(
            following_count=stats["following_count"],
            followers_count=stats["followers_count"],
            is_following=stats["is_following"],
        )

    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        pods, total_count = await self.crud.get_following_pods(user_id, page, size)

        pod_dtos = []
        for pod in pods:
            # 각 파티의 참여자 수와 좋아요 수 계산
            joined_users_count = await self.pod_crud.get_joined_users_count(pod.id)
            like_count = await self.pod_crud.get_like_count(pod.id)

            pod_dto = PodDto.model_validate(pod)
            pod_dto.joinedUsersCount = joined_users_count
            pod_dto.likeCount = like_count

            pod_dtos.append(pod_dto)

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=pod_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserFollowDto]:
        """추천 유저 목록 조회 (현재는 랜덤 유저 반환)"""
        recommended_users = await self.crud.get_recommended_users(user_id, page, size)

        users = []
        for user, tendency_type in recommended_users:
            user_dto = UserFollowDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                tendency_type=tendency_type,
                created_at=None,  # 추천 유저는 팔로우 관계가 없으므로 created_at이 없음
            )
            users.append(user_dto)

        # 추천 유저는 총 개수를 정확히 알 수 없으므로 간단하게 처리
        total_count = len(users)
        total_pages = 1 if total_count > 0 else 0
        has_next = False  # 추천 유저는 한 페이지만 제공
        has_prev = False

        return PageDto(
            items=users,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )
