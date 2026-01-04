from datetime import datetime
from typing import List, Tuple

from app.features.follow.models import Follow
from app.features.tendencies.models import UserTendencyResult
from app.features.users.models import User, UserBlock
from sqlalchemy import and_, desc, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class FollowListRepository:
    """팔로우 목록 조회 Repository"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # - MARK: 팔로우하는 사용자 목록 조회
    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime, str | None]], int]:
        """팔로우하는 사용자 목록 조회"""
        offset = (page - 1) * size

        # 팔로우하는 사용자 목록 조회 (성향 타입 포함, 자기 자신 제외)
        query = (
            select(User, Follow.created_at, UserTendencyResult.tendency_type)
            .join(Follow, User.id == Follow.following_id)
            .outerjoin(UserTendencyResult, User.id == UserTendencyResult.user_id)
            .where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.following_id != user_id,  # 자기 자신 제외
                    Follow.is_active,  # 활성화된 팔로우만
                    ~exists(
                        select(UserBlock.id).where(
                            and_(
                                UserBlock.blocker_id == user_id,
                                UserBlock.blocked_id == User.id,
                            )
                        )
                    ),  # 내가 차단한 사용자 제외
                    ~exists(
                        select(UserBlock.id).where(
                            and_(
                                UserBlock.blocker_id == User.id,
                                UserBlock.blocked_id == user_id,
                            )
                        )
                    ),  # 나를 차단한 사용자 제외
                )
            )
            .order_by(desc(Follow.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self._session.execute(query)
        following_data_raw = result.all()

        # Row 객체를 Tuple로 변환
        following_data: List[Tuple[User, datetime, str | None]] = [
            (row[0], row[1], row[2] if len(row) > 2 else None)
            for row in following_data_raw
        ]

        # 총 팔로우 수 조회 (자기 자신 제외)
        count_query = select(func.count(Follow.id)).where(
            and_(
                Follow.follower_id == user_id,
                Follow.following_id != user_id,  # 자기 자신 제외
                Follow.is_active,
                ~exists(
                    select(UserBlock.id).where(
                        and_(
                            UserBlock.blocker_id == user_id,
                            UserBlock.blocked_id == Follow.following_id,
                        )
                    )
                ),
                ~exists(
                    select(UserBlock.id).where(
                        and_(
                            UserBlock.blocker_id == Follow.following_id,
                            UserBlock.blocked_id == user_id,
                        )
                    )
                ),
            )
        )
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        return following_data, total_count

    # - MARK: 팔로워 목록 조회
    async def get_followers_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime, str | None]], int]:
        """팔로워 목록 조회"""
        offset = (page - 1) * size

        # 팔로워 목록 조회 (성향 타입 포함, 자기 자신 제외)
        query = (
            select(User, Follow.created_at, UserTendencyResult.tendency_type)
            .join(Follow, User.id == Follow.follower_id)
            .outerjoin(UserTendencyResult, User.id == UserTendencyResult.user_id)
            .where(
                and_(
                    Follow.following_id == user_id,
                    Follow.follower_id != user_id,  # 자기 자신 제외
                    Follow.is_active,
                    ~exists(
                        select(UserBlock.id).where(
                            and_(
                                UserBlock.blocker_id == user_id,
                                UserBlock.blocked_id == User.id,
                            )
                        )
                    ),
                    ~exists(
                        select(UserBlock.id).where(
                            and_(
                                UserBlock.blocker_id == User.id,
                                UserBlock.blocked_id == user_id,
                            )
                        )
                    ),
                )
            )
            .order_by(desc(Follow.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self._session.execute(query)
        followers_data_raw = result.all()

        # Row 객체를 Tuple로 변환
        followers_data: List[Tuple[User, datetime, str | None]] = [
            (row[0], row[1], row[2] if len(row) > 2 else None)
            for row in followers_data_raw
        ]

        # 총 팔로워 수 조회 (자기 자신 제외)
        count_query = select(func.count(Follow.id)).where(
            and_(
                Follow.following_id == user_id,
                Follow.follower_id != user_id,  # 자기 자신 제외
                Follow.is_active,
                ~exists(
                    select(UserBlock.id).where(
                        and_(
                            UserBlock.blocker_id == user_id,
                            UserBlock.blocked_id == Follow.follower_id,
                        )
                    )
                ),
                ~exists(
                    select(UserBlock.id).where(
                        and_(
                            UserBlock.blocker_id == Follow.follower_id,
                            UserBlock.blocked_id == user_id,
                        )
                    )
                ),
            )
        )
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        return followers_data, total_count

    # - MARK: 추천 유저 목록 조회
    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> List[Tuple[User, str | None]]:
        """추천 유저 목록 조회 (팔로우/차단한 사용자 제외)"""
        offset = (page - 1) * size

        # 이미 팔로우한 사용자 서브쿼리
        following_subquery = select(Follow.following_id).where(
            and_(Follow.follower_id == user_id, Follow.is_active)
        )

        # 내가 차단한 사용자 서브쿼리
        blocked_by_me_subquery = select(UserBlock.blocked_id).where(
            UserBlock.blocker_id == user_id
        )

        # 나를 차단한 사용자 서브쿼리
        blocked_me_subquery = select(UserBlock.blocker_id).where(
            UserBlock.blocked_id == user_id
        )

        query = (
            select(User, UserTendencyResult.tendency_type)
            .outerjoin(UserTendencyResult, User.id == UserTendencyResult.user_id)
            .where(
                and_(
                    User.id != user_id,  # 자기 자신 제외
                    User.id.notin_(following_subquery),  # 이미 팔로우한 사용자 제외
                    User.id.notin_(blocked_by_me_subquery),  # 내가 차단한 사용자 제외
                    User.id.notin_(blocked_me_subquery),  # 나를 차단한 사용자 제외
                )
            )
            .order_by(func.rand())  # 랜덤 정렬
            .offset(offset)
            .limit(size)
        )

        result = await self._session.execute(query)
        users_raw = result.all()

        # Row 객체를 Tuple로 변환
        users: List[Tuple[User, str | None]] = [
            (row[0], row[1] if len(row) > 1 else None) for row in users_raw
        ]

        return users

    # - MARK: 특정 사용자들이 팔로우하는 사용자 ID 목록 조회
    async def get_following_ids_by_user_ids(
        self, follower_id: int, following_ids: List[int]
    ) -> List[int]:
        """현재 사용자가 팔로우하는 사용자 ID 목록 조회"""
        if not following_ids:
            return []

        query = select(Follow.following_id).where(
            and_(
                Follow.follower_id == follower_id,
                Follow.following_id.in_(following_ids),
                Follow.is_active,
            )
        )
        result = await self._session.execute(query)
        return [row[0] for row in result.all()]
