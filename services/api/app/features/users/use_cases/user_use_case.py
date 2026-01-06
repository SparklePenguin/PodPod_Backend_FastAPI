"""User Use Case - 비즈니스 로직 처리"""

from app.core.security import get_password_hash
from app.features.follow.repositories.follow_repository import FollowRepository
from app.features.follow.services.follow_service import FollowService
from app.features.notifications.repositories.notification_repository import (
    NotificationRepository,
)
from app.features.oauth.schemas import OAuthUserInfo
from app.features.pods.repositories.application_repository import ApplicationRepository
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.tendencies.repositories.tendency_repository import TendencyRepository
from app.features.users.exceptions import (
    EmailAlreadyExistsException,
    EmailRequiredException,
    SameOAuthProviderExistsException,
    UserNotFoundException,
)
from app.features.users.models import User
from app.features.users.repositories import UserRepository
from app.features.users.repositories.user_artist_repository import UserArtistRepository
from app.features.users.repositories.user_notification_repository import (
    UserNotificationRepository,
)
from app.features.users.schemas import (
    UpdateProfileRequest,
    UserDetailDto,
)
from app.features.users.services.user_dto_service import UserDtoService
from app.features.users.services.user_state_service import UserStateService
from sqlalchemy.ext.asyncio import AsyncSession


class UserUseCase:
    """사용자 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        user_artist_repo: UserArtistRepository,
        follow_service: FollowService,
        follow_repo: FollowRepository,
        pod_application_repo: ApplicationRepository,
        pod_repo: PodRepository,
        pod_like_repo: PodLikeRepository,
        notification_repo: NotificationRepository,
        user_notification_repo: UserNotificationRepository,
        tendency_repo: TendencyRepository,
        user_state_service: UserStateService,
        user_dto_service: UserDtoService,
    ):
        self._session = session
        self._user_repo = user_repo
        self._user_artist_repo = user_artist_repo
        self._follow_service = follow_service
        self._follow_repo = follow_repo
        self._pod_application_repo = pod_application_repo
        self._pod_repo = pod_repo
        self._pod_like_repo = pod_like_repo
        self._notification_repo = notification_repo
        self._user_notification_repo = user_notification_repo
        self._tendency_repo = tendency_repo
        self._user_state_service = user_state_service
        self._user_dto_service = user_dto_service

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
        """사용자 생성"""
        # 이메일 필수 체크: OAuth 로그인이 아닌 경우(일반 회원가입)에만 이메일 필수
        if not auth_provider and email is None:
            raise EmailRequiredException()

        # 이메일 중복 확인 (같은 이메일 + 같은 provider 조합 확인)
        user_email = email
        if user_email is not None:
            # 같은 이메일 + 같은 provider 조합으로 조회
            existing_user = await self._user_repo.get_by_email_and_provider(
                user_email, auth_provider
            )
            if existing_user:
                # 같은 이메일 + 같은 provider인 경우
                if auth_provider:
                    # OAuth 로그인: 같은 provider의 계정이 이미 존재
                    raise SameOAuthProviderExistsException(
                        provider=auth_provider or "unknown"
                    )
                else:
                    # 일반 회원가입: 이메일 중복
                    raise EmailAlreadyExistsException(email=user_email)
            # existing_user가 None이면 계속 진행 (새 계정 생성)

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

        # 사용자 생성 (커밋 포함)
        user = await self._create_user(user_dict)

        # UserDetailDto 생성 시 상태 정보 포함
        user_data_dto = await self._prepare_user_dto_data(user, user.id)
        return UserDetailDto.model_validate(user_data_dto, from_attributes=False)

    # - MARK: 사용자 생성 (커밋 포함)
    async def _create_user(self, user_data: dict) -> User:
        """사용자 생성 (커밋 포함)"""
        user = await self._user_repo.create(user_data)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    # - MARK: 사용자 조회
    async def get_user(self, user_id: int) -> UserDetailDto:
        """사용자 조회"""
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
        """프로필 업데이트"""
        update_data = user_data.model_dump(exclude_unset=True)

        # 프로필 업데이트 (커밋 포함)
        user = await self._update_profile(user_id, update_data)
        if not user:
            raise UserNotFoundException(user_id)

        # UserDetailDto 생성 시 상태 정보 포함
        user_dto_data = await self._prepare_user_dto_data(user, user.id)
        return UserDetailDto.model_validate(user_dto_data, from_attributes=False)

    # - MARK: 프로필 업데이트 (커밋 포함)
    async def _update_profile(self, user_id: int, update_data: dict) -> User | None:
        """프로필 업데이트 (커밋 포함)"""
        user = await self._user_repo.update_profile(user_id, update_data)
        if user:
            await self._session.commit()
            await self._session.refresh(user)
        return user

    # - MARK: 약관 동의
    async def accept_terms(
        self, user_id: int, terms_accepted: bool = True
    ) -> UserDetailDto:
        """약관 동의 처리"""
        # 약관 동의 업데이트 (커밋 포함)
        user = await self._update_terms_accepted(user_id, terms_accepted)
        if not user:
            raise UserNotFoundException(user_id)

        # 업데이트된 사용자 정보 조회
        user_data = await self._prepare_user_dto_data(user, user_id)
        return UserDetailDto.model_validate(user_data, from_attributes=False)

    # - MARK: 약관 동의 업데이트 (커밋 포함)
    async def _update_terms_accepted(
        self, user_id: int, terms_accepted: bool
    ) -> User | None:
        """약관 동의 업데이트 (커밋 포함)"""
        user = await self._user_repo.update_terms_accepted(user_id, terms_accepted)
        await self._session.commit()
        if user:
            await self._session.refresh(user)
        return user

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

        # 사용자 정보 업데이트 (커밋 포함)
        restored_user = await self._update_user(user.id, updates)
        if restored_user:
            # user 객체 업데이트를 위해 refresh
            await self._session.refresh(user)

    # - MARK: 사용자 정보 업데이트 (커밋 포함)
    async def _update_user(self, user_id: int, updates: dict) -> User | None:
        """사용자 정보 업데이트 (커밋 포함)"""
        user = await self._user_repo.update_user(user_id, updates)
        await self._session.commit()
        if user:
            await self._session.refresh(user)
        return user

    # - MARK: 유저 FCM 토큰 업데이트
    async def update_fcm_token(
        self, user_id: int, fcm_token: str | None
    ) -> UserDetailDto:
        """유저 FCM 토큰 업데이트"""
        await self._user_repo.update_fcm_token(user_id, fcm_token)
        await self._session.commit()
        # 업데이트된 사용자 정보 반환
        return await self.get_user_with_follow_stats(user_id, user_id)

    # - MARK: 사용자 삭제
    async def delete_user(self, user_id: int) -> None:
        """
        사용자 삭제 (소프트 삭제)
        - 삭제되어도 문제없는 데이터는 삭제
        - 다른 곳에서 조회되거나 문제 생기는 데이터는 isDel로 처리
        """

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
            await self._pod_repo.delete_all_views_by_user_id(user_id)

            # 4. 파티 좋아요 삭제
            await self._pod_like_repo.delete_all_likes_by_user_id(user_id)

            # 5. 파티 멤버십 삭제
            await self._pod_repo.delete_all_members_by_user_id(user_id)

            # 6. 알림 삭제 (user_id와 related_user_id 모두)
            await self._notification_repo.delete_all_by_user_id(user_id)

            # 7. 알림 설정 삭제
            await self._user_notification_repo.delete_by_user_id(user_id)

            # ========== 소프트 삭제 처리 (다른 곳에서 조회 가능한 데이터) ==========
            # 8. 파티장인 파티 처리 - 상태를 CANCELED로 변경
            await self._pod_repo.cancel_pods_by_owner_id(user_id)

            # 9. 팔로우/차단/신고 관계는 유지 (상대방이 볼 수 있으므로)
            # - 팔로우 관계: 유지 (isDel 처리된 사용자도 조회 가능)
            # - 차단 관계: 유지
            # - 신고 관계: 유지 (관리자가 볼 수 있으므로)

            # 10. 파티 후기/평점은 유지 (다른 사람들이 볼 수 있으므로)
            # - PodReview: 유지
            # - PodRating: 유지

            # 11. 사용자 소프트 삭제 처리
            await self._user_repo.soft_delete_user(user_id)

            # 전체 트랜잭션 커밋
            await self._session.commit()
        except Exception:
            # 오류 발생 시 롤백
            await self._session.rollback()
            raise

    # - MARK: UserDetailDto 데이터 준비
    async def _prepare_user_dto_data(
        self, user: User, current_user_id: int | None = None
    ) -> dict:
        """UserDetailDto 생성을 위한 데이터 준비"""
        # 실제 데이터 조회
        # 선호 아티스트 설정 여부 확인
        try:
            artist_ids = await self._user_artist_repo.get_preferred_artist_ids(user.id)
            has_preferred_artists = len(artist_ids) > 0
        except Exception:
            has_preferred_artists = False

        # 성향 테스트 완료 여부 확인
        try:
            user_tendency = await self._tendency_repo.get_user_tendency_result(user.id)
            has_tendency_result = user_tendency is not None
        except Exception:
            has_tendency_result = False

        # 성향 타입 조회
        try:
            user_tendency = await self._tendency_repo.get_user_tendency_result(user.id)
            if user_tendency:
                tendency_type_raw = user_tendency.tendency_type
                tendency_type = (
                    str(tendency_type_raw) if tendency_type_raw is not None else None
                )
            else:
                tendency_type = None
        except Exception:
            tendency_type = None

        # 팔로우 통계 조회 (모든 경우에 포함, 항상 값 제공)
        # commit 후 트랜잭션이 닫혔을 수 있으므로 예외 처리로 기본값 제공
        follow_stats = None
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
        except (Exception, ValueError):
            # 팔로로우 통계 조회 실패 시 None으로 유지 (기본값은 UserDtoService에서 처리)
            pass

        # UserDtoService를 사용하여 데이터 준비
        return await self._user_dto_service.prepare_user_dto_data(
            user=user,
            has_preferred_artists=has_preferred_artists,
            has_tendency_result=has_tendency_result,
            tendency_type=tendency_type,
            follow_stats=follow_stats,
            user_state_service=self._user_state_service,
        )
