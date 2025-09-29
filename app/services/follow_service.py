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
from app.core.error_codes import get_error_info


class FollowService:
    """팔로우 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = FollowCRUD(db)
        self.pod_crud = PodCRUD(db)

    async def follow_user(self, follower_id: int, followingId: int) -> FollowResponse:
        """사용자 팔로우"""
        follow = await self.crud.create_follow(follower_id, followingId)

        if not follow:
            raise ValueError("팔로우에 실패했습니다.")

        return FollowResponse.model_validate(follow)

    async def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """사용자 팔로우 취소"""
        return await self.crud.delete_follow(follower_id, following_id)

    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> FollowListResponse:
        """팔로우하는 사용자 목록 조회"""
        following_data, total_count = await self.crud.get_following_list(
            user_id, page, size
        )

        users = []
        for user, created_at in following_data:
            user_dto = UserFollowDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                created_at=created_at,
            )
            users.append(user_dto)

        has_next = (page * size) < total_count

        return FollowListResponse(
            users=users,
            totalCount=total_count,
            page=page,
            size=size,
            hasNext=has_next,
        )

    async def get_followers_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> FollowListResponse:
        """팔로워 목록 조회"""
        followers_data, total_count = await self.crud.get_followers_list(
            user_id, page, size
        )

        users = []
        for user, created_at in followers_data:
            user_dto = UserFollowDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                created_at=created_at,
            )
            users.append(user_dto)

        has_next = (page * size) < total_count

        return FollowListResponse(
            users=users,
            totalCount=total_count,
            page=page,
            size=size,
            hasNext=has_next,
        )

    async def get_follow_stats(
        self, user_id: int, current_user_id: Optional[int] = None
    ) -> FollowStatsResponse:
        """팔로우 통계 조회"""
        stats = await self.crud.get_follow_stats(user_id, current_user_id)

        return FollowStatsResponse(
            followingCount=stats["following_count"],
            followersCount=stats["followers_count"],
            isFollowing=stats["is_following"],
        )

    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> List[PodDto]:
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

        return pod_dtos

    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> List[UserFollowDto]:
        """추천 유저 목록 조회 (현재는 랜덤 유저 반환)"""
        recommended_users = await self.crud.get_recommended_users(user_id, page, size)

        users = []
        for user in recommended_users:
            user_dto = UserFollowDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                created_at=user.created_at,
            )
            users.append(user_dto)

        return users
