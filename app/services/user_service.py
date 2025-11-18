from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import UserCRUD
from app.crud.artist import ArtistCRUD
from app.crud.user_block import UserBlockCRUD
from app.crud.follow import FollowCRUD
from app.crud.pod.pod_application import PodApplicationCRUD
from app.schemas.common import BaseResponse
from app.schemas.user import (
    UpdateProfileRequest,
    UserDto,
    UserDtoInternal,
    BlockUserResponse,
)
from app.schemas.follow import SimpleUserDto
from app.schemas.auth import SignUpRequest
from app.schemas.artist import ArtistDto
from app.schemas.common.page_dto import PageDto
from app.core.security import get_password_hash
from app.models.user_state import UserState
from typing import List, Optional

from app.core.error_codes import raise_error
from app.services.follow_service import FollowService


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_crud = UserCRUD(db)
        self.artist_crud = ArtistCRUD(db)
        self.follow_service = FollowService(db)
        self.block_crud = UserBlockCRUD(db)
        self.follow_crud = FollowCRUD(db)
        self.pod_application_crud = PodApplicationCRUD(db)
        self.db = db

        # - MARK: 사용자 생성

    async def create_user(self, user_data: SignUpRequest) -> UserDto:
        # 이메일 중복 확인 (provider도 함께 확인)
        existing_user = await self.user_crud.get_by_email(user_data.email)
        if existing_user:
            # 같은 provider인지 확인
            if (
                user_data.auth_provider
                and existing_user.auth_provider == user_data.auth_provider
                and existing_user.auth_provider_id == user_data.auth_provider_id
            ):
                # 같은 provider의 같은 계정이면 중복 에러
                raise_error("SAME_OAUTH_PROVIDER_EXISTS")
            elif not user_data.auth_provider:
                # OAuth가 없는 경우(일반 회원가입)에는 이메일 중복 에러
                raise_error("EMAIL_ALREADY_EXISTS")
            else:
                # 다른 OAuth provider인 경우 계속 진행 (새 계정 생성)
                pass

        # 비밀번호 해싱
        if user_data.password is not None:
            hashed_password = get_password_hash(user_data.password)
        else:
            hashed_password = None  # 소셜 로그인의 경우

        # 사용자 생성
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password

        user = await self.user_crud.create(user_dict)

        # Sendbird 사용자 생성
        try:
            from app.services.sendbird_service import SendbirdService
            import logging

            logger = logging.getLogger(__name__)
            sendbird_service = SendbirdService()

            sendbird_success = await sendbird_service.create_user(
                user_id=str(user.id),
                nickname=user.nickname or "사용자",
                profile_url=user.profile_image or "",
            )

            if sendbird_success:
                logger.info(f"사용자 {user.id} Sendbird 유저 생성 성공")
            else:
                logger.warning(f"사용자 {user.id} Sendbird 유저 생성 실패")

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"사용자 {user.id} Sendbird 유저 생성 중 오류: {e}")
            # Sendbird 생성 실패는 무시하고 계속 진행

        # UserDto 생성 시 상태 정보 포함
        user_data = await self._prepare_user_dto_data(user, user.id)
        return UserDto.model_validate(user_data, from_attributes=False)

    # - MARK: OAuth 사용자 조회
    async def get_user_by_auth_provider_id(
        self, auth_provider: str, auth_provider_id: str
    ) -> Optional[UserDto]:
        """OAuth 프로바이더 ID로 사용자 조회"""
        user = await self.user_crud.get_by_auth_provider_id(
            auth_provider, auth_provider_id
        )
        if not user or user.is_del:
            return None

        # UserDto 생성 시 상태 정보 포함
        user_data = await self._prepare_user_dto_data(user, user.id)
        return UserDto.model_validate(user_data, from_attributes=False)

    # - MARK: (내부용) 사용자 목록 조회
    async def get_users(self) -> List[UserDtoInternal]:
        users = await self.user_crud.get_all()
        return [
            UserDtoInternal.model_validate(user, from_attributes=True) for user in users
        ]

    # - MARK: 사용자 조회
    async def get_user(self, user_id: int) -> UserDto:
        user = await self.user_crud.get_by_id(user_id)
        if not user or user.is_del:
            raise_error("USER_NOT_FOUND")

        # UserDto 생성 시 상태 정보 포함
        user_data = await self._prepare_user_dto_data(user, user.id)
        return UserDto.model_validate(user_data, from_attributes=False)

    # - MARK: 사용자 조회 (팔로우 통계 포함)
    async def get_user_with_follow_stats(
        self, user_id: int, current_user_id: int
    ) -> UserDto:
        """다른 사용자 정보 조회 (팔로우 통계 포함)"""
        user = await self.user_crud.get_by_id(user_id)
        if not user or user.is_del:
            raise_error("USER_NOT_FOUND")

        # UserDto 생성 시 상태 정보 및 팔로우 통계 포함
        user_data = await self._prepare_user_dto_data(user, current_user_id)
        return UserDto.model_validate(user_data, from_attributes=False)

    # - MARK: (내부용) 사용자 조회 (모든 정보 포함)
    async def get_user_internal(self, user_id: int) -> UserDtoInternal:
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise_error("USER_NOT_FOUND")

        return UserDtoInternal.model_validate(user, from_attributes=True)

    # - MARK: 프로필 업데이트
    async def update_profile(
        self, user_id: int, user_data: UpdateProfileRequest
    ) -> UserDto:
        update_data = user_data.model_dump(exclude_unset=True)

        user = await self.user_crud.update_profile(user_id, update_data)
        if not user:
            raise_error("USER_NOT_FOUND")

        # Sendbird 사용자 프로필 업데이트
        try:
            from app.services.sendbird_service import SendbirdService

            sendbird_service = SendbirdService()

            # Sendbird에 업데이트할 필드만 추출
            sendbird_nickname = update_data.get("nickname")
            sendbird_profile_url = update_data.get("profile_image")

            # Sendbird 업데이트 (비동기로 실행, 실패해도 메인 로직은 계속)
            await sendbird_service.update_user_profile(
                user_id=str(user_id),
                nickname=sendbird_nickname,
                profile_url=sendbird_profile_url,
            )
        except Exception as e:
            # Sendbird 업데이트 실패는 로그만 남기고 메인 로직은 계속
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Sendbird 사용자 프로필 업데이트 실패 (user_id: {user_id}): {e}"
            )

        # UserDto 생성 시 상태 정보 포함
        user_data = await self._prepare_user_dto_data(user, user.id)
        return UserDto.model_validate(user_data, from_attributes=False)

    # - MARK: 선호 아티스트 조회
    async def get_preferred_artists(self, user_id: int) -> List[ArtistDto]:
        """사용자의 선호 아티스트 목록 조회"""
        # 아티스트 ID 목록 가져오기
        artist_ids = await self.user_crud.get_preferred_artist_ids(user_id)

        # 각 아티스트 정보 가져오기
        artists = []
        for artist_id in artist_ids:
            artist = await self.artist_crud.get_by_id(artist_id)
            if artist:
                artists.append(ArtistDto.model_validate(artist, from_attributes=True))

        return artists

    # - MARK: 선호 아티스트 업데이트 (추가/제거)
    async def update_preferred_artists(
        self, user_id: int, artist_ids: List[int]
    ) -> List[ArtistDto]:
        """선호 아티스트 목록을 완전히 교체하여 업데이트"""
        # 아티스트 존재 확인
        for artist_id in artist_ids:
            artist = await self.artist_crud.get_by_id(artist_id)
            if not artist:
                raise_error(
                    "ARTIST_NOT_FOUND", additional_data={"artist_id": artist_id}
                )

        # 기존 선호 아티스트 모두 제거
        current_artist_ids = await self.user_crud.get_preferred_artist_ids(user_id)
        for current_artist_id in current_artist_ids:
            await self.user_crud.remove_preferred_artist(user_id, current_artist_id)

        # 새로운 선호 아티스트 추가
        for artist_id in artist_ids:
            await self.user_crud.add_preferred_artist(user_id, artist_id)

        # 업데이트된 선호 아티스트 목록 반환
        return await self.get_preferred_artists(user_id)

    def _determine_user_state(
        self, user, has_preferred_artists: bool, has_tendency_result: bool
    ) -> UserState:
        """사용자 온보딩 상태 결정"""
        # 1. 선호 아티스트가 없으면 PREFERRED_ARTISTS
        if not has_preferred_artists:
            return UserState.PREFERRED_ARTISTS

        # 2. 성향 테스트 결과가 없으면 TENDENCY_TEST
        if not has_tendency_result:
            return UserState.TENDENCY_TEST

        # 3. 닉네임이 없으면 PROFILE_SETTING
        if not user.nickname:
            return UserState.PROFILE_SETTING

        # 4. 모든 조건을 만족하면 COMPLETED
        return UserState.COMPLETED

    async def _has_preferred_artists(self, user_id: int) -> bool:
        """사용자가 선호 아티스트를 설정했는지 확인"""
        try:
            preferred_artists = await self.get_preferred_artists(user_id)
            return len(preferred_artists) > 0
        except:
            return False

    async def _has_tendency_result(self, user_id: int) -> bool:
        """사용자가 성향 테스트를 완료했는지 확인"""
        # UserTendencyResult 테이블에서 해당 user_id의 결과가 있는지 확인
        from sqlalchemy import select
        from app.models.tendency import UserTendencyResult

        try:
            result = await self.db.execute(
                select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
            )
            user_tendency = result.scalar_one_or_none()
            return user_tendency is not None
        except Exception as e:
            print(f"성향 결과 확인 오류 (user_id: {user_id}): {e}")
            return False

    async def _get_user_tendency_type(self, user_id: int) -> Optional[str]:
        """사용자의 성향 타입 조회"""
        from sqlalchemy import select
        from app.models.tendency import UserTendencyResult

        try:
            result = await self.db.execute(
                select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
            )
            user_tendency = result.scalar_one_or_none()
            if user_tendency:
                return user_tendency.tendency_type
            return None
        except Exception as e:
            print(f"성향 타입 조회 오류 (user_id: {user_id}): {e}")
            return None

    async def _prepare_user_dto_data(self, user, current_user_id: int = None) -> dict:
        """UserDto 생성을 위한 데이터 준비"""
        # 기본 사용자 정보
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "intro": user.intro,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        # 실제 데이터 조회
        has_preferred_artists = await self._has_preferred_artists(user.id)
        has_tendency_result = await self._has_tendency_result(user.id)

        # 사용자 상태 결정
        user_data["state"] = self._determine_user_state(
            user, has_preferred_artists, has_tendency_result
        )

        # 성향 타입 추가
        user_data["tendency_type"] = await self._get_user_tendency_type(user.id)

        # 팔로우 통계 추가 (모든 경우에 포함)
        try:
            if current_user_id and current_user_id != user.id:
                # 다른 사용자 정보 조회 시: 팔로우 여부 포함
                follow_stats = await self.follow_service.get_follow_stats(
                    user.id, current_user_id
                )
            else:
                # 본인 정보 조회 시: 팔로우 여부 없이 통계만
                follow_stats = await self.follow_service.get_follow_stats(user.id, None)
            user_data["follow_stats"] = follow_stats
            user_data["is_following"] = follow_stats.is_following
        except Exception:
            # 팔로우 통계 조회 실패 시 None으로 설정
            user_data["follow_stats"] = None
            user_data["is_following"] = False

        return user_data

    # - MARK: 사용자 차단
    async def block_user(
        self, blocker_id: int, blocked_id: int
    ) -> Optional[BlockUserResponse]:
        """사용자 차단 (팔로우 관계도 함께 삭제)"""
        # 차단할 사용자 존재 확인
        blocked_user = await self.user_crud.get_by_id(blocked_id)
        if not blocked_user:
            return None

        # 차단 생성
        block = await self.block_crud.create_block(blocker_id, blocked_id)
        if not block:
            return None

        # 팔로우 관계 삭제 (양방향 모두)
        # 1. 내가 차단한 사람을 팔로우하고 있었다면 팔로우 해제
        await self.follow_crud.delete_follow(blocker_id, blocked_id)

        # 2. 차단한 사람이 나를 팔로우하고 있었다면 팔로우 해제
        await self.follow_crud.delete_follow(blocked_id, blocker_id)

        return BlockUserResponse(
            blocker_id=block.blocker_id,
            blocked_id=block.blocked_id,
            created_at=block.created_at,
        )

    async def unblock_user(self, blocker_id: int, blocked_id: int) -> bool:
        """사용자 차단 해제"""
        return await self.block_crud.delete_block(blocker_id, blocked_id)

    async def get_blocked_users(
        self, blocker_id: int, page: int = 1, size: int = 20
    ) -> PageDto[SimpleUserDto]:
        """차단한 사용자 목록 조회"""
        blocked_data, total_count = await self.block_crud.get_blocked_users(
            blocker_id, page, size
        )

        users = []
        for user, blocked_at in blocked_data:
            # 성향 타입 조회
            tendency_type = await self._get_user_tendency_type(user.id)

            user_dto = SimpleUserDto(
                id=user.id,
                nickname=user.nickname,
                profile_image=user.profile_image,
                intro=user.intro,
                tendency_type=tendency_type,
                is_following=False,  # 차단한 사용자는 팔로우할 수 없음
            )
            users.append(user_dto)

        # PageDto 생성
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1

        return PageDto(
            items=users,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    async def check_block_exists(self, blocker_id: int, blocked_id: int) -> bool:
        """차단 관계 존재 여부 확인"""
        return await self.block_crud.check_block_exists(blocker_id, blocked_id)

    async def delete_user(self, user_id: int) -> None:
        """
        사용자 삭제 (소프트 삭제)
        - 삭제되어도 문제없는 데이터는 삭제
        - 다른 곳에서 조회되거나 문제 생기는 데이터는 isDel로 처리
        """
        from sqlalchemy import delete, update, select
        from app.models.notification import Notification
        from app.models.user_notification_settings import UserNotificationSettings
        from app.models.pod import PodLike, PodMember, PodView, Pod
        from app.models.pod.pod_status import PodStatus
        from app.models.user import User

        # 사용자 존재 확인
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise_error("USER_NOT_FOUND")

        # 이미 삭제된 사용자인지 확인
        if user.is_del:
            return

        # ========== 삭제 가능한 데이터 (개인 데이터) ==========
        # 1. 선호 아티스트 삭제
        preferred_artist_ids = await self.user_crud.get_preferred_artist_ids(user_id)
        for artist_id in preferred_artist_ids:
            await self.user_crud.remove_preferred_artist(user_id, artist_id)

        # 2. 파티 신청서 삭제
        await self.pod_application_crud.delete_all_by_user_id(user_id)

        # 3. 파티 조회 기록 삭제
        await self.db.execute(delete(PodView).where(PodView.user_id == user_id))
        await self.db.commit()

        # 4. 파티 좋아요 삭제
        await self.db.execute(delete(PodLike).where(PodLike.user_id == user_id))
        await self.db.commit()

        # 5. 파티 멤버십 삭제
        await self.db.execute(delete(PodMember).where(PodMember.user_id == user_id))
        await self.db.commit()

        # 6. 알림 삭제 (user_id와 sender_id 모두)
        await self.db.execute(
            delete(Notification).where(
                (Notification.user_id == user_id) | (Notification.sender_id == user_id)
            )
        )
        await self.db.commit()

        # 7. 알림 설정 삭제
        await self.db.execute(
            delete(UserNotificationSettings).where(
                UserNotificationSettings.user_id == user_id
            )
        )
        await self.db.commit()

        # ========== 소프트 삭제 처리 (다른 곳에서 조회 가능한 데이터) ==========
        # 8. 파티장인 파티 처리 - 상태를 CANCELED로 변경
        pods_query = select(Pod).where(Pod.owner_id == user_id)
        pods_result = await self.db.execute(pods_query)
        owner_pods = pods_result.scalars().all()

        for pod in owner_pods:
            pod.status = PodStatus.CANCELED
            pod.is_active = False
        await self.db.commit()

        # 9. 팔로우/차단/신고 관계는 유지 (상대방이 볼 수 있으므로)
        # - 팔로우 관계: 유지 (isDel 처리된 사용자도 조회 가능)
        # - 차단 관계: 유지
        # - 신고 관계: 유지 (관리자가 볼 수 있으므로)

        # 10. 파티 후기/평점은 유지 (다른 사람들이 볼 수 있으므로)
        # - PodReview: 유지
        # - PodRating: 유지

        # 11. 사용자 소프트 삭제 처리
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_del=True,
                is_active=False,
                nickname=None,  # 개인정보 삭제
                email=None,
                profile_image=None,
                intro=None,
                fcm_token=None,
            )
        )
        await self.db.commit()
