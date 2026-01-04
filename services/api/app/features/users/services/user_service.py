from app.core.security import get_password_hash
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.oauth.schemas.oauth_user_info import OAuthUserInfo
from app.features.pods.repositories.application_repository import (
    ApplicationRepository,
)
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.users.exceptions import (
    EmailAlreadyExistsException,
    EmailRequiredException,
    SameOAuthProviderExistsException,
    UserNotFoundException,
)
from app.features.users.models import User, UserState
from app.features.users.repositories import UserRepository
from app.features.users.repositories.user_artist_repository import UserArtistRepository
from app.features.users.schemas import (
    UpdateProfileRequest,
    UserDetailDto,
    UserDto,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(self, session: AsyncSession):
        self._user_repo = UserRepository(session)
        from app.core.services.fcm_service import FCMService
        from app.features.follow.services.follow_service import FollowService

        self._follow_service = FollowService(session, fcm_service=FCMService())
        self._follow_repo = FollowRepository(session)
        self._pod_application_repo = ApplicationRepository(session)
        self._tendency_repo = TendencyRepository(session)
        self._user_artist_repo = UserArtistRepository(session)
        self._session = session

    # - MARK: 유저 복구
    async def restore_user(self, user: User, oauth_user_info: OAuthUserInfo | None):
        """유저 소프트 삭제 복구(is_del 플래그)"""
        updates = {"is_del": False}
        if oauth_user_info:
            if oauth_user_info.nickname:
                updates["nickname"] = oauth_user_info.nickname
            if oauth_user_info.image_url:
                updates["profile_image"] = oauth_user_info.image_url
            if oauth_user_info.email:
                updates["email"] = oauth_user_info.email

        restored_user = await self._user_repo.update_user(user.id, updates)
        if restored_user:
            # user 객체 업데이트를 위해 refresh
            await self._session.refresh(user)

    # - MARK: 유저 FCM 토큰 업데이트
    async def update_fcm_token(
        self, user_id: int, fcm_token: str | None
    ) -> UserDetailDto:
        """유저 FCM 토큰 업데이트"""
        await self._user_repo.update_fcm_token(user_id, fcm_token)
        # 업데이트된 사용자 정보 반환
        return await self.get_user_with_follow_stats(user_id, user_id)

    # - MARK: 사용자 생성
    async def create_user(
        self,
        email: str | None,
        name: str | None = None,
        nickname: str | None = None,
        profile_image: str | None = None,
        auth_provider: str | None = None,
        auth_provider_id: str | None = None,
        fcm_token: str | None = None,
        password: str | None = None,
    ) -> UserDetailDto:
        # 이메일 필수 체크: OAuth 로그인이 아닌 경우(일반 회원가입)에만 이메일 필수
        if not auth_provider and email is None:
            raise EmailRequiredException()

        # 이메일 중복 확인 (이메일이 있고, provider도 함께 확인)
        user_email = email
        if user_email is not None:
            existing_user = await self._user_repo.get_by_email(user_email)
            if existing_user:
                # 같은 provider인지 확인
                existing_auth_provider = existing_user.auth_provider
                existing_auth_provider_id = existing_user.auth_provider_id

                if (
                    auth_provider
                    and existing_auth_provider == auth_provider
                    and existing_auth_provider_id == auth_provider_id
                ):
                    # 같은 provider의 같은 계정이면 중복 에러
                    raise SameOAuthProviderExistsException(
                        provider=auth_provider or "unknown"
                    )
                elif not auth_provider:
                    # OAuth가 없는 경우(일반 회원가입)에는 이메일 중복 에러
                    raise EmailAlreadyExistsException(email=user_email)
                else:
                    # 다른 OAuth provider인 경우 계속 진행 (새 계정 생성)
                    pass

        # 비밀번호 해싱
        if password is not None:
            hashed_password = get_password_hash(password)
        else:
            hashed_password = None  # 소셜 로그인의 경우

        # 사용자 생성
        user_dict = {
            "email": email,
            "username": name,
            "nickname": nickname,
            "profile_image": profile_image,
            "auth_provider": auth_provider,
            "auth_provider_id": auth_provider_id,
            "fcm_token": fcm_token,
            "hashed_password": hashed_password,
        }
        # None 값 제거
        user_dict = {k: v for k, v in user_dict.items() if v is not None}

        user = await self._user_repo.create(user_dict)

        # UserDetailDto 생성 시 상태 정보 포함
        user_data_dto = await self._prepare_user_dto_data(user, user.id)
        return UserDetailDto.model_validate(user_data_dto, from_attributes=False)

    # - MARK: 사용자 조회
    async def get_user(self, user_id: int) -> UserDetailDto:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        if user.is_del:
            raise UserNotFoundException(user_id)

        # UserDetailDto 생성 시 상태 정보 포함
        user_data = await self._prepare_user_dto_data(user, user.id)
        return UserDetailDto.model_validate(user_data, from_attributes=False)

    # - MARK: 사용자 조회 (팔로우 통계 포함)
    async def get_user_with_follow_stats(
        self, user_id: int, current_user_id: int
    ) -> UserDetailDto:
        """다른 사용자 정보 조회 (팔로우 통계 포함)"""
        # commit 후 세션이 닫혔을 수 있으므로 항상 새로 조회
        # expire_on_commit=False로 설정되어 있어도 안전하게 새로 조회
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        if user.is_del:
            raise UserNotFoundException(user_id)

        # UserDetailDto 생성 시 상태 정보 및 팔로우 통계 포함
        user_data = await self._prepare_user_dto_data(user, current_user_id)
        return UserDetailDto.model_validate(user_data, from_attributes=False)

    # - MARK: 프로필 업데이트
    async def update_profile(
        self, user_id: int, user_data: UpdateProfileRequest
    ) -> UserDetailDto:
        update_data = user_data.model_dump(exclude_unset=True)

        user = await self._user_repo.update_profile(user_id, update_data)
        if not user:
            raise UserNotFoundException(user_id)

        # UserDetailDto 생성 시 상태 정보 포함
        user_dto_data = await self._prepare_user_dto_data(user, user.id)
        return UserDetailDto.model_validate(user_dto_data, from_attributes=False)

    # - MARK: 사용자 온보딩 상태 결정
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

    # - MARK: 선호 아티스트 설정 여부 확인
    async def _has_preferred_artists(self, user_id: int) -> bool:
        """사용자가 선호 아티스트를 설정했는지 확인"""
        try:
            artist_ids = await self._user_artist_repo.get_preferred_artist_ids(user_id)
            return len(artist_ids) > 0
        except Exception:
            return False

    # - MARK: 성향 테스트 완료 여부 확인
    async def _has_tendency_result(self, user_id: int) -> bool:
        """사용자가 성향 테스트를 완료했는지 확인"""
        try:
            user_tendency = await self._tendency_repo.get_user_tendency_result(user_id)
            return user_tendency is not None
        except Exception:
            return False

    # - MARK: 사용자 성향 타입 조회
    async def _get_user_tendency_type(self, user_id: int) -> str | None:
        """사용자의 성향 타입 조회"""
        try:
            user_tendency = await self._tendency_repo.get_user_tendency_result(user_id)
            if user_tendency:
                tendency_type_raw = user_tendency.tendency_type
                return str(tendency_type_raw) if tendency_type_raw is not None else None
            return None
        except Exception:
            return None

    # - MARK: UserDto 생성
    def create_user_dto(
        self, user: User | None, tendency_type: str = "", is_following: bool = False
    ) -> UserDto:
        """User 모델과 성향 타입으로 UserDto 생성 (재사용 가능)"""
        if not user:
            return UserDto(
                id=0,
                nickname="",
                profile_image="",
                intro="",
                tendency_type=tendency_type,
                is_following=is_following,
            )

        return UserDto(
            id=user.id or 0,
            nickname=user.nickname or "",
            profile_image=user.profile_image or "",
            intro=user.intro or "",
            tendency_type=tendency_type,
            is_following=is_following,
        )

    # - MARK: UserDetailDto 데이터 준비
    async def _prepare_user_dto_data(
        self, user, current_user_id: int | None = None
    ) -> dict:
        """UserDetailDto 생성을 위한 데이터 준비"""
        import datetime
        from datetime import timezone

        # 기본 사용자 정보
        # created_at과 updated_at은 항상 값이 있어야 하므로 None 체크
        now = datetime.datetime.now(timezone.utc)
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "intro": user.intro,
            "terms_accepted": user.terms_accepted,
            "created_at": user.created_at if user.created_at is not None else now,
            "updated_at": user.updated_at if user.updated_at is not None else now,
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

        # 팔로우 통계 추가 (모든 경우에 포함, 항상 값 제공)
        # commit 후 트랜잭션이 닫혔을 수 있으므로 예외 처리로 기본값 제공
        try:
            # 세션 상태 확인
            if not self._session.is_active:
                raise ValueError("Session is not active")

            if current_user_id and current_user_id != user.id:
                # 다른 사용자 정보 조회 시: 팔로우 여부 포함
                follow_stats = await self._follow_service.get_follow_stats(
                    user.id, current_user_id
                )
            else:
                # 본인 정보 조회 시: 팔로우 여부 없이 통계만
                follow_stats = await self._follow_service.get_follow_stats(
                    user.id, None
                )
            user_data["follow_stats"] = follow_stats
            user_data["is_following"] = follow_stats.is_following
        except (Exception, ValueError):
            # 팔로로우 통계 조회 실패 시 기본값 제공 (세션이 닫혔거나 다른 오류)
            from app.features.follow.schemas import FollowStatsDto

            user_data["follow_stats"] = FollowStatsDto(
                following_count=0, followers_count=0, is_following=False
            )
            user_data["is_following"] = False

        return user_data

    # - MARK: 약관 동의
    async def accept_terms(
        self, user_id: int, terms_accepted: bool = True
    ) -> UserDetailDto:
        """약관 동의 처리"""
        # 약관 동의 업데이트 (repo 메서드 사용)
        user = await self._user_repo.update_terms_accepted(user_id, terms_accepted)
        if not user:
            raise UserNotFoundException(user_id)

        # 업데이트된 사용자 정보 조회
        user_data = await self._prepare_user_dto_data(user, user_id)
        return UserDetailDto.model_validate(user_data, from_attributes=False)

    # - MARK: 사용자 삭제
    async def delete_user(self, user_id: int) -> None:
        """
        사용자 삭제 (소프트 삭제)
        - 삭제되어도 문제없는 데이터는 삭제
        - 다른 곳에서 조회되거나 문제 생기는 데이터는 isDel로 처리
        """
        from app.features.notifications.models.notification import Notification
        from app.features.pods.models import (
            Pod,
            PodLike,
            PodMember,
            PodStatus,
            PodView,
        )
        from app.features.users.models import UserNotificationSettings
        from sqlalchemy import delete

        # 사용자 존재 확인
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        # 이미 삭제된 사용자인지 확인
        if user.is_del:
            return

        # 트랜잭션 시작 (모든 삭제 작업을 하나의 트랜잭션으로 처리)
        try:
            # ========== 삭제 가능한 데이터 (개인 데이터) ==========
            # 1. 선호 아티스트 삭제
            await self._user_artist_repo.remove_all_preferred_artists(user_id)

            # 2. 파티 신청서 삭제
            await self._pod_application_repo.delete_all_by_user_id(user_id)

            # 3. 파티 조회 기록 삭제
            await self._session.execute(
                delete(PodView).where(PodView.user_id == user_id)
            )

            # 4. 파티 좋아요 삭제
            await self._session.execute(
                delete(PodLike).where(PodLike.user_id == user_id)
            )

            # 5. 파티 멤버십 삭제
            await self._session.execute(
                delete(PodMember).where(PodMember.user_id == user_id)
            )

            # 6. 알림 삭제 (user_id와 related_user_id 모두)
            await self._session.execute(
                delete(Notification).where(
                    (Notification.user_id == user_id)
                    | (Notification.related_user_id == user_id)
                )
            )

            # 7. 알림 설정 삭제
            await self._session.execute(
                delete(UserNotificationSettings).where(
                    UserNotificationSettings.user_id == user_id
                )
            )

            # ========== 소프트 삭제 처리 (다른 곳에서 조회 가능한 데이터) ==========
            # 8. 파티장인 파티 처리 - 상태를 CANCELED로 변경
            pods_query = select(Pod).where(Pod.owner_id == user_id)
            pods_result = await self._session.execute(pods_query)
            owner_pods = pods_result.scalars().all()

            for pod in owner_pods:
                if pod:
                    status_value = (
                        PodStatus.CANCELED.value
                        if hasattr(PodStatus.CANCELED, "value")
                        else str(PodStatus.CANCELED)
                    )
                    pod.status = status_value
                    pod.is_active = False

            # 9. 팔로우/차단/신고 관계는 유지 (상대방이 볼 수 있으므로)
            # - 팔로우 관계: 유지 (isDel 처리된 사용자도 조회 가능)
            # - 차단 관계: 유지
            # - 신고 관계: 유지 (관리자가 볼 수 있으므로)

            # 10. 파티 후기/평점은 유지 (다른 사람들이 볼 수 있으므로)
            # - PodReview: 유지
            # - PodRating: 유지

            # 11. 사용자 소프트 삭제 처리
            await self._session.execute(
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
                    terms_accepted=False,  # 약관 동의 초기화
                )
            )

            # commit은 use_case에서 처리
        except Exception:
            # 오류 발생 시 롤백
            await self._session.rollback()
            raise
