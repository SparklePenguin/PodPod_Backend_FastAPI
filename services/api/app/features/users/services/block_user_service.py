from datetime import datetime, timezone

from app.common.schemas import PageDto
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.tendencies.use_cases.tendency_use_case import TendencyUseCase
from app.features.users.exceptions import (
    BlockNotFoundException,
    CannotBlockSelfException,
    UserNotFoundException,
)
from app.features.users.repositories import BlockUserRepository, UserRepository
from app.features.users.schemas import BlockUserResponse, UserDto
from sqlalchemy.ext.asyncio import AsyncSession


class BlockUserService:
    """사용자 차단 서비스"""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._block_repo = BlockUserRepository(session)
        self._user_repo = UserRepository(session)
        self._follow_repo = FollowRepository(session)
        tendency_repo = TendencyRepository(session)
        self._tendency_use_case = TendencyUseCase(session, tendency_repo)

    # - MARK: 사용자 성향 타입 조회
    async def _get_user_tendency_type(self, user_id: int) -> str | None:
        """사용자의 성향 타입 조회"""
        try:
            user_tendency = await self._tendency_use_case.get_user_tendency_result(
                user_id
            )
            if user_tendency:
                return user_tendency.tendency_type
            return None
        except Exception:
            return None

    # - MARK: 사용자 차단
    async def block_user(self, blocker_id: int, blocked_id: int) -> BlockUserResponse:
        """사용자 차단 (팔로우 관계도 함께 삭제)"""
        # 자기 자신을 차단하려는 경우
        if blocker_id == blocked_id:
            raise CannotBlockSelfException()

        # 차단할 사용자 존재 확인
        blocked_user = await self._user_repo.get_by_id(blocked_id)
        if not blocked_user:
            raise UserNotFoundException(blocked_id)

        # 차단 생성
        block = await self._block_repo.create_block(blocker_id, blocked_id)
        if not block:
            raise UserNotFoundException(blocked_id)

        # 팔로우 관계 삭제 (양방향 모두)
        # 1. 내가 차단한 사람을 팔로우하고 있었다면 팔로우 해제
        await self._follow_repo.delete_follow(blocker_id, blocked_id)

        # 2. 차단한 사람이 나를 팔로우하고 있었다면 팔로우 해제
        await self._follow_repo.delete_follow(blocked_id, blocker_id)

        # datetime 기본값 제공
        created_at_val = (
            block.created_at
            if block.created_at is not None
            else datetime.now(timezone.utc).replace(tzinfo=None)
        )

        return BlockUserResponse(
            blocker_id=block.blocker_id,
            blocked_id=block.blocked_id,
            created_at=created_at_val,
        )

    # - MARK: 사용자 차단 해제
    async def unblock_user(self, blocker_id: int, blocked_id: int) -> None:
        """사용자 차단 해제"""
        success = await self._block_repo.delete_block(blocker_id, blocked_id)
        if not success:
            raise BlockNotFoundException()

    # - MARK: 차단한 사용자 목록 조회
    async def get_blocked_users(
        self, blocker_id: int, page: int = 1, size: int = 20
    ) -> PageDto[UserDto]:
        """차단한 사용자 목록 조회"""
        blocked_data, total_count = await self._block_repo.get_blocked_users(
            blocker_id, page, size
        )

        users = []
        for user, blocked_at in blocked_data:
            # 성향 타입 조회
            if user.id is None:
                continue
            tendency_type = await self._get_user_tendency_type(user.id)

            user_dto = UserDto(
                id=user.id,
                nickname=user.nickname or "",
                profile_image=user.profile_image or "",
                intro=user.intro or "",
                tendency_type=tendency_type or "",
                is_following=False,  # 차단한 사용자는 팔로우할 수 없음
            )
            users.append(user_dto)

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=users,
            page=page,
            size=size,
            total=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )
