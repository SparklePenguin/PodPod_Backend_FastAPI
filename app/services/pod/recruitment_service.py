from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod.pod import PodCRUD
from app.crud.pod.recruitment import RecruitmentCRUD
from app.crud.pod.pod_application import PodApplicationCRUD
from app.core.error_codes import raise_error
from app.schemas.pod.pod_application_dto import PodApplicationDto
from app.schemas.follow import SimpleUserDto
from app.models.user import User
from app.services.fcm_service import FCMService
import logging

logger = logging.getLogger(__name__)


class RecruitmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pod_crud = PodCRUD(db)
        self.crud = RecruitmentCRUD(db)
        self.application_crud = PodApplicationCRUD(db)

    # - MARK: 파티 참여 신청
    async def apply_to_pod(
        self, pod_id: int, user_id: int, message: str = None
    ) -> PodApplicationDto:
        pod = await self.pod_crud.get_pod_by_id(pod_id)
        if pod is None:
            raise_error("POD_NOT_FOUND")

        # Pod 정보를 미리 로드하여 세션 분리 문제 방지
        pod_owner_id = pod.owner_id

        # 이미 멤버인지 확인 (비동기 조회)
        pod_members = await self.crud.list_members(pod_id)
        already_member = any(m.user_id == user_id for m in pod_members)
        if already_member:
            raise_error("ALREADY_MEMBER")

        # 파티 참여 신청서 생성
        try:
            application = await self.application_crud.create_application(
                pod_id, user_id, message
            )
            # Application 정보를 미리 로드하여 세션 분리 문제 방지
            application_id = application.id
            application_pod_id = application.pod_id
            application_message = application.message
            application_status = application.status
            application_applied_at = application.applied_at
            application_reviewed_at = application.reviewed_at
        except ValueError as e:
            if "이미 신청한 파티입니다" in str(e):
                raise_error("ALREADY_APPLIED")
            raise e

        # User 정보 가져오기 (필요한 필드들을 미리 로드)
        from sqlalchemy import select

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise_error("USER_NOT_FOUND")

        # 사용자 정보를 미리 로드하여 세션 분리 문제 방지
        user_nickname = user.nickname
        user_profile_image = user.profile_image
        user_intro = user.intro

        # 성향 타입 조회
        from app.models.tendency import UserTendencyResult

        result = await self.db.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        user_tendency = result.scalar_one_or_none()
        tendency_type = user_tendency.tendency_type if user_tendency else None

        # 파티장에게 FCM 알림 전송
        try:
            # 캐시 완전 무효화를 위해 새 세션으로 조회

            # 세션 캐시 무효화
            self.db.expire_all()

            result = await self.db.execute(select(User).where(User.id == pod_owner_id))
            owner = result.scalar_one_or_none()

            if owner and owner.fcm_token:
                logger.info(
                    f"파티장 {owner.id}의 FCM 토큰으로 알림 전송 시도: {owner.fcm_token[:20]}..."
                )
                fcm_service = FCMService()
                await fcm_service.send_pod_join_request(
                    token=owner.fcm_token,
                    nickname=user_nickname,
                    pod_id=pod_id,
                    db=self.db,
                    user_id=owner.id,
                    related_user_id=user_id,
                )
                logger.info(
                    f"파티장 {owner.id}에게 파티 참여 신청 알림 전송 완료 (신청자: {user_nickname})"
                )
            else:
                logger.info(
                    f"파티장 {pod_owner_id}의 FCM 토큰이 없어서 알림을 전송하지 않습니다. (토큰: {owner.fcm_token if owner else 'None'})"
                )
        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            # 알림 전송 실패는 무시하고 계속 진행

        # PodApplicationDto로 변환하여 반환 (SQLAlchemy lazy loading 방지)
        # 이미 위에서 로드한 사용자 정보를 사용

        user_dto = SimpleUserDto(
            id=user_id,
            nickname=user_nickname,
            profile_image=user_profile_image,
            intro=user_intro,
            tendency_type=tendency_type,
            is_following=False,
        )

        # 이미 위에서 로드한 application 정보를 사용

        return PodApplicationDto(
            id=application_id,
            podId=application_pod_id,
            user=user_dto,
            message=application_message,
            status=application_status,
            appliedAt=application_applied_at,
            reviewedAt=application_reviewed_at,
            reviewedBy=None,  # 아직 검토되지 않음
        )

    # - MARK: 신청서 승인/거절
    async def review_application(
        self, application_id: int, status: str, reviewed_by: int
    ) -> PodApplicationDto:
        # 신청서 승인/거절 처리
        application = await self.application_crud.review_application(
            application_id, status, reviewed_by
        )

        # application 속성들을 미리 로드 (SQLAlchemy lazy loading 방지)
        application_pod_id = application.pod_id
        application_user_id = application.user_id
        application_message = application.message
        application_status = application.status
        application_applied_at = application.applied_at
        application_reviewed_at = application.reviewed_at

        # 승인된 경우 멤버로 추가 (대소문자 구분 없이)
        if status.lower() == "approved":
            try:

                await self.crud.add_member(
                    application_pod_id,
                    application_user_id,
                    role="member",
                    message=application_message,
                )

                # 샌드버드 채팅방에 멤버 초대
                try:
                    pod = await self.pod_crud.get_pod_by_id(application_pod_id)
                    if pod and pod.chat_channel_url:
                        from app.services.sendbird_service import SendbirdService

                        sendbird_service = SendbirdService()
                        success = await sendbird_service.join_channel(
                            channel_url=pod.chat_channel_url,
                            user_ids=[str(application_user_id)],
                        )

                        if success:
                            logger.info(
                                f"신청자 {application_user_id}를 샌드버드 채팅방 {pod.chat_channel_url}에 초대 완료"
                            )
                        else:
                            logger.warning(
                                f"신청자 {application_user_id} 샌드버드 채팅방 초대 실패"
                            )
                    else:
                        logger.warning(
                            f"파티 {application_pod_id}의 채팅방 URL이 없어 샌드버드 초대 건너뜀"
                        )

                except Exception as e:
                    logger.error(f"샌드버드 채팅방 초대 실패: {e}")
                    # 샌드버드 초대 실패는 무시하고 계속 진행

            except ValueError as e:
                if "파티 정원이 가득 찼습니다" in str(e):
                    raise_error("POD_IS_FULL")
                elif "이미" in str(e) and "멤버" in str(e):
                    # 이미 멤버인 경우는 무시하고 계속 진행
                    pass
                else:
                    raise e

        # User 정보 가져오기
        user = await self.db.get(User, application_user_id)
        reviewer = await self.db.get(User, reviewed_by) if reviewed_by else None

        # user 속성들을 미리 로드 (SQLAlchemy lazy loading 방지)
        if user:
            user_id = user.id
            user_nickname = user.nickname
            user_profile_image = user.profile_image
            user_intro = user.intro
        else:
            user_id = None
            user_nickname = None
            user_profile_image = None
            user_intro = None

        # 신청자에게 FCM 알림 전송 (승인/거절)
        try:
            if user and user.fcm_token:
                pod = await self.pod_crud.get_pod_by_id(application_pod_id)
                fcm_service = FCMService()

                if status.lower() == "approved":
                    # 승인 알림
                    await fcm_service.send_pod_request_approved(
                        token=user.fcm_token,
                        party_name=pod.title if pod else "파티",
                        pod_id=application.pod_id,
                        db=self.db,
                        user_id=user.id,
                        related_user_id=reviewed_by,
                        related_pod_id=application_pod_id,
                    )
                    logger.info(f"신청자 {user.id}에게 파티 승인 알림 전송 완료")
                elif status.lower() == "rejected":
                    # 거절 알림
                    await fcm_service.send_pod_request_rejected(
                        token=user.fcm_token,
                        party_name=pod.title if pod else "파티",
                        pod_id=application_pod_id,
                        db=self.db,
                        user_id=user.id,
                        related_user_id=reviewed_by,
                        related_pod_id=application_pod_id,
                    )
                    logger.info(f"신청자 {user.id}에게 파티 거절 알림 전송 완료")

                    # 좋아요한 파티에 자리 생김 알림 전송
                    await self._send_spot_opened_notifications(application_pod_id, pod)
        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            # 알림 전송 실패는 무시하고 계속 진행

        # 신청자 성향 타입 조회
        from sqlalchemy import select
        from app.models.tendency import UserTendencyResult

        result = await self.db.execute(
            select(UserTendencyResult).where(
                UserTendencyResult.user_id == application_user_id
            )
        )
        user_tendency = result.scalar_one_or_none()
        user_tendency_type = user_tendency.tendency_type if user_tendency else None

        # 검토자 성향 타입 조회
        reviewer_tendency_type = None
        if reviewer:
            result = await self.db.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == reviewed_by
                )
            )
            reviewer_tendency = result.scalar_one_or_none()
            reviewer_tendency_type = (
                reviewer_tendency.tendency_type if reviewer_tendency else None
            )

        # SimpleUserDto 생성
        user_dto = SimpleUserDto(
            id=user_id,
            nickname=user_nickname,
            profile_image=user_profile_image,
            intro=user_intro,
            tendency_type=user_tendency_type,
            is_following=False,
        )

        reviewer_dto = None
        if reviewer:
            # reviewer 속성들을 미리 로드 (SQLAlchemy lazy loading 방지)
            reviewer_id = reviewer.id
            reviewer_nickname = reviewer.nickname
            reviewer_profile_image = reviewer.profile_image
            reviewer_intro = reviewer.intro

            reviewer_dto = SimpleUserDto(
                id=reviewer_id,
                nickname=reviewer_nickname,
                profile_image=reviewer_profile_image,
                intro=reviewer_intro,
                tendency_type=reviewer_tendency_type,
                is_following=False,
            )

        # PodApplicationDto로 변환하여 반환
        return PodApplicationDto(
            id=application_id,
            podId=application_pod_id,
            user=user_dto,
            message=application_message,
            status=application_status,
            appliedAt=application_applied_at,
            reviewedAt=application_reviewed_at,
            reviewedBy=reviewer_dto,
        )

    # - MARK: 신청서 취소 (application_id 사용)
    async def cancel_application_by_id(self, application_id: int, user_id: int) -> bool:
        # 신청서 조회
        application = await self.application_crud.get_application_by_id(application_id)

        if not application:
            raise_error("POD_NOT_FOUND")  # 신청서를 찾을 수 없음

        # 본인의 신청서인지 확인
        if application.user_id != user_id:
            raise_error("NO_POD_ACCESS_PERMISSION")  # 권한 없음

        # pending 상태만 취소 가능
        if application.status != "pending":
            raise_error("POD_ALREADY_CLOSED")  # 이미 처리된 신청서

        # 신청서 삭제
        return await self.application_crud.delete_application(application_id)

    # - MARK: 파티 탈퇴
    async def leave_pod(self, pod_id: int, user_id: int) -> bool:
        """파티에서 탈퇴 (파티장은 탈퇴 불가)"""
        # 파티 조회
        pod = await self.pod_crud.get_pod_by_id(pod_id)
        if not pod:
            raise_error("POD_NOT_FOUND")

        # 파티장은 탈퇴 불가
        if pod.owner_id == user_id:
            raise_error("NO_POD_ACCESS_PERMISSION")  # 파티장은 탈퇴할 수 없습니다

        # 멤버 삭제
        result = await self.crud.remove_member(pod_id, user_id)

        # 파티 탈퇴 시 좋아요한 파티에 자리 생김 알림 전송
        if result:
            await self._send_spot_opened_notifications(pod_id, pod)

        return result

    # - MARK: 좋아요한 파티에 자리 생김 알림
    async def _send_spot_opened_notifications(self, pod_id: int, pod) -> None:
        """파티에 자리가 생겼을 때 좋아요한 사용자들에게 알림 전송"""
        try:
            if not pod:
                return

            # 해당 파티를 좋아요한 사용자들 조회
            from sqlalchemy import select
            from app.models.pod.pod_like import PodLike
            from app.models.user import User

            likes_query = (
                select(User)
                .join(PodLike, User.id == PodLike.user_id)
                .where(PodLike.pod_id == pod_id)
                .distinct()
            )

            likes_result = await self.db.execute(likes_query)
            liked_users = likes_result.scalars().all()

            if not liked_users:
                logger.info(f"파티 {pod_id}를 좋아요한 사용자가 없음")
                return

            # FCM 서비스 초기화
            fcm_service = FCMService()

            # 각 좋아요한 사용자에게 알림 전송
            for user in liked_users:
                try:
                    if user.fcm_token:
                        await fcm_service.send_saved_pod_spot_opened(
                            token=user.fcm_token,
                            party_name=pod.title,
                            pod_id=pod_id,
                            db=self.db,
                            user_id=user.id,
                        )
                        logger.info(
                            f"좋아요한 파티 자리 생김 알림 전송 성공: user_id={user.id}, pod_id={pod_id}"
                        )
                    else:
                        logger.warning(f"FCM 토큰이 없는 사용자: user_id={user.id}")

                except Exception as e:
                    logger.error(
                        f"좋아요한 파티 자리 생김 알림 전송 실패: user_id={user.id}, error={e}"
                    )

        except Exception as e:
            logger.error(
                f"좋아요한 파티 자리 생김 알림 처리 중 오류: pod_id={pod_id}, error={e}"
            )
