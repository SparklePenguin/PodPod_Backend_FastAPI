"""User DTO Service - UserDto 및 UserDetailDto 생성 로직"""

import datetime
from datetime import timezone
from typing import TYPE_CHECKING

from app.features.follow.schemas import FollowStatsDto
from app.features.users.models import User
from app.features.users.schemas import UserDto

if TYPE_CHECKING:
    from app.features.users.services.user_state_service import UserStateService


class UserDtoService:
    """User DTO 생성 서비스"""

    @staticmethod
    def create_user_dto(
        user: User | None, tendency_type: str | None = None, is_following: bool = False
    ) -> UserDto:
        """User 모델로 UserDto 생성 (재사용 가능)
        
        tendency_type이 None인 경우 user.tendency_type 사용
        """
        if not user:
            return UserDto(
                id=0,
                nickname="",
                profile_image="",
                intro="",
                tendency_type=tendency_type or "",
                is_following=is_following,
            )

        # tendency_type이 None이면 user.tendency_type 사용
        final_tendency_type = tendency_type if tendency_type is not None else (user.tendency_type or "")

        return UserDto(
            id=user.id or 0,
            nickname=user.nickname or "",
            profile_image=user.profile_image or "",
            intro=user.intro or "",
            tendency_type=final_tendency_type,
            is_following=is_following,
        )

    @staticmethod
    async def prepare_user_dto_data(
        user: User,
        has_preferred_artists: bool,
        has_tendency_result: bool,
        tendency_type: str | None,
        follow_stats: FollowStatsDto | None,
        user_state_service: "UserStateService",
    ) -> dict:
        """UserDetailDto 생성을 위한 데이터 준비"""
        # 기본 사용자 정보
        # created_at과 updated_at은 항상 값이 있어야 하므로 None 체크
        now = datetime.datetime.now(timezone.utc)
        detail = user.detail
        user_data = {
            "id": user.id,
            "email": detail.email if detail else None,
            "username": detail.username if detail else None,
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "intro": user.intro,
            "terms_accepted": detail.terms_accepted if detail else False,
            "created_at": user.created_at if user.created_at is not None else now,
            "updated_at": user.updated_at if user.updated_at is not None else now,
        }

        # 사용자 상태 결정
        user_data["state"] = user_state_service.determine_state(
            user, has_preferred_artists, has_tendency_result
        )

        # 성향 타입 추가
        user_data["tendency_type"] = tendency_type

        # 팔로우 통계 추가
        if follow_stats:
            user_data["follow_stats"] = follow_stats
            user_data["is_following"] = follow_stats.is_following
        else:
            # 기본값 제공
            user_data["follow_stats"] = FollowStatsDto(
                following_count=0, followers_count=0, is_following=False
            )
            user_data["is_following"] = False

        return user_data
