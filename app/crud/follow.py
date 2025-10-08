from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime
from app.models.follow import Follow
from app.models.user import User
from app.models.pod.pod import Pod
from app.models.tendency import UserTendencyResult


class FollowCRUD:
    """팔로우 CRUD 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_follow(
        self, follower_id: int, following_id: int
    ) -> Optional[Follow]:
        """팔로우 생성"""
        try:
            # 자기 자신을 팔로우하는지 확인
            if follower_id == following_id:
                return None

            # 이미 팔로우하고 있는지 확인
            existing_follow = await self.get_follow(follower_id, following_id)
            if existing_follow:
                return existing_follow

            follow = Follow(follower_id=follower_id, following_id=following_id)
            self.db.add(follow)
            await self.db.commit()
            await self.db.refresh(follow)
            return follow
        except Exception:
            await self.db.rollback()
            return None

    async def delete_follow(self, follower_id: int, following_id: int) -> bool:
        """팔로우 취소"""
        try:
            follow = await self.get_follow(follower_id, following_id)
            if not follow:
                return False

            await self.db.delete(follow)
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False

    async def get_follow(self, follower_id: int, following_id: int) -> Optional[Follow]:
        """특정 팔로우 조회"""
        query = select(Follow).where(
            and_(Follow.follower_id == follower_id, Follow.following_id == following_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def check_follow_exists(self, follower_id: int, following_id: int) -> bool:
        """팔로우 관계 존재 여부 확인"""
        query = select(Follow).where(
            and_(Follow.follower_id == follower_id, Follow.following_id == following_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_following_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime, Optional[str]]], int]:
        """팔로우하는 사용자 목록 조회"""
        offset = (page - 1) * size

        # 팔로우하는 사용자 목록 조회 (성향 타입 포함)
        query = (
            select(User, Follow.created_at, UserTendencyResult.tendency_type)
            .join(Follow, User.id == Follow.following_id)
            .outerjoin(UserTendencyResult, User.id == UserTendencyResult.user_id)
            .where(Follow.follower_id == user_id)
            .order_by(desc(Follow.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        following_data = result.all()

        # 총 팔로우 수 조회
        count_query = select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        return following_data, total_count

    async def get_followers_list(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Tuple[User, datetime, Optional[str]]], int]:
        """팔로워 목록 조회"""
        offset = (page - 1) * size

        # 팔로워 목록 조회 (성향 타입 포함)
        query = (
            select(User, Follow.created_at, UserTendencyResult.tendency_type)
            .join(Follow, User.id == Follow.follower_id)
            .outerjoin(UserTendencyResult, User.id == UserTendencyResult.user_id)
            .where(Follow.following_id == user_id)
            .order_by(desc(Follow.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        followers_data = result.all()

        # 총 팔로워 수 조회
        count_query = select(func.count(Follow.id)).where(
            Follow.following_id == user_id
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        return followers_data, total_count

    async def get_follow_stats(
        self, user_id: int, current_user_id: Optional[int] = None
    ) -> dict:
        """팔로우 통계 조회"""
        # 팔로우하는 수
        following_count_query = select(func.count(Follow.id)).where(
            Follow.follower_id == user_id
        )
        following_count_result = await self.db.execute(following_count_query)
        following_count = following_count_result.scalar()

        # 팔로워 수
        followers_count_query = select(func.count(Follow.id)).where(
            Follow.following_id == user_id
        )
        followers_count_result = await self.db.execute(followers_count_query)
        followers_count = followers_count_result.scalar()

        # 현재 사용자가 해당 사용자를 팔로우하는지 확인
        is_following = False
        if current_user_id and current_user_id != user_id:
            follow = await self.get_follow(current_user_id, user_id)
            is_following = follow is not None

        return {
            "following_count": following_count,
            "followers_count": followers_count,
            "is_following": is_following,
        }

    async def get_following_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[Pod], int]:
        """팔로우하는 사용자가 만든 파티 목록 조회"""
        offset = (page - 1) * size

        # 팔로우하는 사용자들이 만든 파티 조회
        query = (
            select(Pod)
            .join(Follow, Pod.owner_id == Follow.following_id)
            .where(Follow.follower_id == user_id)
            .order_by(desc(Pod.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        pods = result.scalars().all()

        # 총 파티 수 조회
        count_query = (
            select(func.count(Pod.id))
            .join(Follow, Pod.owner_id == Follow.following_id)
            .where(Follow.follower_id == user_id)
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        return pods, total_count

    async def get_recommended_users(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> List[Tuple[User, Optional[str]]]:
        """추천 유저 목록 조회 (현재는 랜덤 유저 반환)"""
        offset = (page - 1) * size

        # 현재 사용자가 팔로우하지 않은 다른 사용자들을 랜덤으로 조회 (성향 타입 포함)
        subquery = select(Follow.following_id).where(Follow.follower_id == user_id)

        query = (
            select(User, UserTendencyResult.tendency_type)
            .outerjoin(UserTendencyResult, User.id == UserTendencyResult.user_id)
            .where(
                and_(
                    User.id != user_id,  # 자기 자신 제외
                    User.id.notin_(subquery),  # 이미 팔로우한 사용자 제외
                )
            )
            .order_by(func.rand())  # 랜덤 정렬
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        users = result.all()

        return users

    async def get_notification_status(
        self, follower_id: int, following_id: int
    ) -> Optional[bool]:
        """특정 팔로우 관계의 알림 설정 상태 조회"""
        follow = await self.get_follow(follower_id, following_id)
        if not follow:
            return None
        return follow.notification_enabled

    async def update_notification_status(
        self, follower_id: int, following_id: int, notification_enabled: bool
    ) -> bool:
        """특정 팔로우 관계의 알림 설정 상태 변경"""
        try:
            follow = await self.get_follow(follower_id, following_id)
            if not follow:
                return False

            follow.notification_enabled = notification_enabled
            await self.db.commit()
            await self.db.refresh(follow)
            return True
        except Exception:
            await self.db.rollback()
            return False
