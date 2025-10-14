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
        except ValueError as e:
            if "이미 신청한 파티입니다" in str(e):
                raise_error("ALREADY_APPLIED")
            raise e

        # User 정보 가져오기
        user = await self.db.get(User, user_id)

        # 성향 타입 조회
        from sqlalchemy import select
        from app.models.tendency import UserTendencyResult

        result = await self.db.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        user_tendency = result.scalar_one_or_none()
        tendency_type = user_tendency.tendency_type if user_tendency else None

        # 파티장에게 FCM 알림 전송
        try:
            owner = await self.db.get(User, pod.owner_id)
            if owner and owner.fcm_token:
                fcm_service = FCMService()
                await fcm_service.send_pod_join_request(
                    token=owner.fcm_token,
                    nickname=user.nickname,
                    pod_id=pod_id,
                    db=self.db,
                    user_id=owner.id,
                    related_user_id=user_id,
                )
                logger.info(
                    f"파티장 {owner.id}에게 파티 참여 신청 알림 전송 완료 (신청자: {user.nickname})"
                )
        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            # 알림 전송 실패는 무시하고 계속 진행

        # PodApplicationDto로 변환하여 반환
        user_dto = SimpleUserDto(
            id=user.id,
            nickname=user.nickname,
            profile_image=user.profile_image,
            intro=user.intro,
            tendency_type=tendency_type,
            is_following=False,
        )

        return PodApplicationDto(
            id=application.id,
            podId=application.pod_id,
            user=user_dto,
            message=application.message,
            status=application.status,
            appliedAt=application.applied_at,
            reviewedAt=application.reviewed_at,
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

        # 승인된 경우 멤버로 추가 (대소문자 구분 없이)
        if status.lower() == "approved":
            try:
                await self.crud.add_member(
                    application.pod_id,
                    application.user_id,
                    role="member",
                    message=application.message,
                )

                # 샌드버드 채팅방에 멤버 초대
                try:
                    pod = await self.pod_crud.get_pod_by_id(application.pod_id)
                    if pod and pod.chat_channel_url:
                        from app.services.sendbird_service import SendbirdService

                        sendbird_service = SendbirdService()
                        success = await sendbird_service.join_channel(
                            channel_url=pod.chat_channel_url,
                            user_ids=[str(application.user_id)],
                        )

                        if success:
                            logger.info(
                                f"신청자 {application.user_id}를 샌드버드 채팅방 {pod.chat_channel_url}에 초대 완료"
                            )
                        else:
                            logger.warning(
                                f"신청자 {application.user_id} 샌드버드 채팅방 초대 실패"
                            )
                    else:
                        logger.warning(
                            f"파티 {application.pod_id}의 채팅방 URL이 없어 샌드버드 초대 건너뜀"
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
        user = await self.db.get(User, application.user_id)
        reviewer = await self.db.get(User, reviewed_by) if reviewed_by else None

        # 신청자에게 FCM 알림 전송 (승인/거절)
        try:
            if user and user.fcm_token:
                pod = await self.pod_crud.get_pod_by_id(application.pod_id)
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
                        related_pod_id=application.pod_id,
                    )
                    logger.info(f"신청자 {user.id}에게 파티 승인 알림 전송 완료")
                elif status.lower() == "rejected":
                    # 거절 알림
                    await fcm_service.send_pod_request_rejected(
                        token=user.fcm_token,
                        party_name=pod.title if pod else "파티",
                        pod_id=application.pod_id,
                        db=self.db,
                        user_id=user.id,
                        related_user_id=reviewed_by,
                        related_pod_id=application.pod_id,
                    )
                    logger.info(f"신청자 {user.id}에게 파티 거절 알림 전송 완료")
        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            # 알림 전송 실패는 무시하고 계속 진행

        # 신청자 성향 타입 조회
        from sqlalchemy import select
        from app.models.tendency import UserTendencyResult

        result = await self.db.execute(
            select(UserTendencyResult).where(
                UserTendencyResult.user_id == application.user_id
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
            id=user.id,
            nickname=user.nickname,
            profile_image=user.profile_image,
            intro=user.intro,
            tendency_type=user_tendency_type,
            is_following=False,
        )

        reviewer_dto = None
        if reviewer:
            reviewer_dto = SimpleUserDto(
                id=reviewer.id,
                nickname=reviewer.nickname,
                profile_image=reviewer.profile_image,
                intro=reviewer.intro,
                tendency_type=reviewer_tendency_type,
                is_following=False,
            )

        # PodApplicationDto로 변환하여 반환
        return PodApplicationDto(
            id=application.id,
            podId=application.pod_id,
            user=user_dto,
            message=application.message,
            status=application.status,
            appliedAt=application.applied_at,
            reviewedAt=application.reviewed_at,
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
        return await self.crud.remove_member(pod_id, user_id)
