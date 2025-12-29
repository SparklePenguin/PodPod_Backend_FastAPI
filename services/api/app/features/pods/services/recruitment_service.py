import logging
from typing import cast

from app.core.services.fcm_service import FCMService
from app.features.pods.exceptions import (
    AlreadyAppliedException,
    AlreadyMemberException,
    NoPodAccessPermissionException,
    PodAlreadyClosedException,
    PodIsFullException,
    PodNotFoundException,
)
from app.features.pods.models.pod.pod_status import PodStatus
from app.features.pods.repositories.application_repository import (
    PodApplicationRepository,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.recruitment_repository import RecruitmentRepository
from app.features.pods.schemas.pod_appl_detail_dto import PodApplDetailDto
from app.features.users.models import User
from app.features.users.schemas import UserDto
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RecruitmentService:
    def __init__(self, session: AsyncSession, fcm_service: FCMService | None = None):
        self._session = session
        self._pod_repo = PodRepository(self._session)
        self._recruitment_repo = RecruitmentRepository(self._session)
        self._application_repo = PodApplicationRepository(self._session)
        self._fcm_service = fcm_service or FCMService()

    # - MARK: 파티 참여 신청
    async def apply_to_pod(
        self, pod_id: int, user_id: int, message: str | None = None
    ) -> PodApplDetailDto:
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if pod is None:
            raise PodNotFoundException(pod_id)

        # Pod 정보를 미리 로드하여 세션 분리 문제 방지
        if pod.owner_id is None:
            raise PodNotFoundException(pod_id)

        # 이미 멤버인지 확인 (비동기 조회)
        pod_members = await self._recruitment_repo.list_members(pod_id)
        already_member = any(m.user_id == user_id for m in pod_members)
        if already_member:
            raise AlreadyMemberException(pod_id, user_id)

        # 파티 참여 신청서 생성
        try:
            application = await self._application_repo.create_application(
                pod_id, user_id, message
            )
            # Application 정보를 미리 로드하여 세션 분리 문제 방지
            application_id = application.id or 0
            application_pod_id = application.pod_id or 0
            application_message = application.message
            application_status = application.status or ""
            application_applied_at = application.applied_at or 0
            application_reviewed_at = application.reviewed_at
        except ValueError as e:
            if "이미 신청한 파티입니다" in str(e):
                raise AlreadyAppliedException(pod_id, user_id)
            raise e

        # User 정보 가져오기 (필요한 필드들을 미리 로드)
        from sqlalchemy import select

        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            from app.features.users.exceptions import UserNotFoundException

            raise UserNotFoundException(user_id)

        # 사용자 정보를 미리 로드하여 세션 분리 문제 방지
        user_nickname = user.nickname or ""
        user_profile_image = user.profile_image or ""
        user_intro = user.intro or ""

        # 성향 타입 조회
        from app.features.tendencies.models import UserTendencyResult

        result = await self._session.execute(
            select(UserTendencyResult).where(UserTendencyResult.user_id == user_id)
        )
        user_tendency = result.scalar_one_or_none()
        tendency_type_raw = user_tendency.tendency_type if user_tendency else None
        tendency_type = str(tendency_type_raw) if tendency_type_raw is not None else ""

        # 파티장에게 FCM 알림 전송
        try:
            # 캐시 완전 무효화를 위해 새 세션으로 조회

            # 세션 캐시 무효화
            self._session.expire_all()

            result = await self._session.execute(
                select(User).where(User.id == pod.owner_id)
            )
            owner = result.scalar_one_or_none()

            if owner and owner.fcm_token:
                logger.info(
                    f"파티장 {owner.id}의 FCM 토큰으로 알림 전송 시도: {owner.fcm_token[:20]}..."
                )
                await self._fcm_service.send_pod_join_request(
                    token=owner.fcm_token,
                    nickname=user_nickname,
                    pod_id=pod_id,
                    db=self._db,
                    user_id=owner.id,
                    related_user_id=user_id,
                )
                logger.info(
                    f"파티장 {owner.id}에게 파티 참여 신청 알림 전송 완료 (신청자: {user_nickname})"
                )
            else:
                logger.info(
                    f"파티장 {pod.owner_id}의 FCM 토큰이 없어서 알림을 전송하지 않습니다. (토큰: {owner.fcm_token if owner else 'None'})"
                )
        except Exception as e:
            logger.error(f"FCM 알림 전송 실패: {e}")
            # 알림 전송 실패는 무시하고 계속 진행

        # PodApplDetailDto로 변환하여 반환 (SQLAlchemy lazy loading 방지)
        # 이미 위에서 로드한 사용자 정보를 사용

        user_dto = UserDto(
            id=user_id,
            nickname=user_nickname,
            profile_image=user_profile_image,
            intro=user_intro,
            tendency_type=tendency_type,
            is_following=False,
        )

        # 이미 위에서 로드한 application 정보를 사용

        return PodApplDetailDto(
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
    ) -> PodApplDetailDto:
        # 신청서 승인/거절 처리
        application = await self._application_repo.review_application(
            application_id, status, reviewed_by
        )

        # application 속성들을 미리 로드 (SQLAlchemy lazy loading 방지)
        application_pod_id = application.pod_id or 0
        application_user_id = application.user_id or 0
        application_message = application.message
        application_status = application.status or ""
        application_applied_at = application.applied_at or 0
        application_reviewed_at = application.reviewed_at

        # 승인된 경우 멤버로 추가 (대소문자 구분 없이)
        if status.lower() == "approved":
            try:
                # 파티 정보 조회 (인원 확인용)
                pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                if not pod:
                    raise PodNotFoundException(application_pod_id)

                application_message_str = (
                    str(application_message)
                    if application_message is not None
                    else None
                )
                await self._recruitment_repo.add_member(
                    application_pod_id,
                    application_user_id,
                    role="member",
                    message=application_message_str,
                )

                # add_member 후 실제 멤버 수를 다시 조회하여 정확히 확인
                # (add_member 내부에서 커밋이 일어났으므로 최신 상태 확인 필요)
                # 세션 캐시 무효화하여 최신 데이터 조회
                self._session.expire_all()

                updated_pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                if not updated_pod:
                    logger.error(f"파티를 찾을 수 없음: pod_id={application_pod_id}")
                    raise PodNotFoundException(application_pod_id)

                # get_joined_users_count를 사용하여 owner 포함 총 인원수 정확히 계산
                actual_member_count = await self._pod_repo.get_joined_users_count(
                    application_pod_id
                )

                updated_pod_capacity = updated_pod.capacity or 0
                updated_pod_status = updated_pod.status
                logger.info(
                    f"[파티 승낙 후 인원 확인] pod_id={application_pod_id}, "
                    f"actual_member_count={actual_member_count}, capacity={updated_pod_capacity}, "
                    f"status={updated_pod_status}"
                )

                # 새 멤버 참여 알림 전송 (파티장, 신청자 제외 참여 유저)
                await self._send_new_member_notification(
                    application_pod_id, application_user_id
                )

                # 샌드버드 채팅방에 멤버 초대
                try:
                    pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                    if pod and pod.chat_channel_url:
                        from app.core.services.sendbird_service import SendbirdService

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
                    raise PodIsFullException(application_pod_id)
                elif "이미" in str(e) and "멤버" in str(e):
                    # 이미 멤버인 경우는 무시하고 계속 진행
                    pass
                else:
                    raise e

        # User 정보 가져오기
        user = await self._session.get(User, application_user_id)
        reviewer = await self._session.get(User, reviewed_by) if reviewed_by else None

        # user 속성들을 미리 로드 (SQLAlchemy lazy loading 방지)
        if user:
            user_id = user.id
            user_nickname = user.nickname or ""
            user_profile_image = user.profile_image or ""
            user_intro = user.intro or ""
        else:
            user_id = None
            user_nickname = ""
            user_profile_image = ""
            user_intro = ""

        # 신청자에게 FCM 알림 전송 (승인/거절)
        try:
            if user and user.fcm_token:
                pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                pod_title = pod.title or "" if pod else "파티"

                if status.lower() == "approved":
                    # 승인 알림
                    await self._fcm_service.send_pod_request_approved(
                        token=user.fcm_token,
                        party_name=pod_title,
                        pod_id=application_pod_id,
                        db=self._db,
                        user_id=user.id,
                        related_user_id=reviewed_by,
                        related_pod_id=application_pod_id,
                    )
                    logger.info(f"신청자 {user.id}에게 파티 승인 알림 전송 완료")

                    # 정원 가득 참 알림 전송 (승인 알림 이후)
                    # 다시 파티 정보를 조회하여 최신 상태 확인
                    final_pod = await self._pod_repo.get_pod_by_id(application_pod_id)
                    if final_pod:
                        final_member_count = (
                            await self._pod_repo.get_joined_users_count(
                                application_pod_id
                            )
                        )
                        final_pod_capacity = final_pod.capacity or 0
                        final_pod_status = final_pod.status
                        if (
                            final_member_count >= final_pod_capacity
                            or final_pod_status == PodStatus.COMPLETED
                        ):
                            logger.info(
                                f"[파티 정원 가득 참] 알림 전송 시작: pod_id={application_pod_id}, "
                                f"final_member_count={final_member_count}, capacity={final_pod_capacity}, "
                                f"status={final_pod_status}"
                            )
                            await self._send_capacity_full_notification(
                                application_pod_id, final_pod
                            )
                elif status.lower() == "rejected":
                    # 거절 알림
                    await self._fcm_service.send_pod_request_rejected(
                        token=user.fcm_token,
                        party_name=pod_title,
                        pod_id=application_pod_id,
                        db=self._db,
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
        from app.features.tendencies.models import UserTendencyResult
        from sqlalchemy import select

        result = await self._session.execute(
            select(UserTendencyResult).where(
                UserTendencyResult.user_id == application_user_id
            )
        )
        user_tendency = result.scalar_one_or_none()
        user_tendency_type_raw = user_tendency.tendency_type if user_tendency else None
        user_tendency_type = (
            str(user_tendency_type_raw) if user_tendency_type_raw is not None else ""
        )

        # 검토자 성향 타입 조회
        reviewer_tendency_type: str = ""
        if reviewer:
            result = await self._session.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == reviewed_by
                )
            )
            reviewer_tendency = result.scalar_one_or_none()
            reviewer_tendency_type_raw = (
                reviewer_tendency.tendency_type if reviewer_tendency else None
            )
            reviewer_tendency_type = (
                str(reviewer_tendency_type_raw)
                if reviewer_tendency_type_raw is not None
                else ""
            )

        # SimpleUserDto 생성
        user_id_val = user_id or 0
        user_dto = UserDto(
            id=user_id_val,
            nickname=user_nickname,
            profile_image=user_profile_image,
            intro=user_intro,
            tendency_type=user_tendency_type,
            is_following=False,
        )

        reviewer_dto = None
        if reviewer:
            reviewer_intro = reviewer.intro or ""
            reviewer_dto = UserDto(
                id=reviewer.id or 0,
                nickname=reviewer.nickname or "",
                profile_image=reviewer.profile_image or "",
                intro=reviewer_intro,
                tendency_type=reviewer_tendency_type,
                is_following=False,
            )

        # PodApplDetailDto로 변환하여 반환
        application_status_str = str(application_status) if application_status else ""
        application_message_str = (
            str(application_message) if application_message is not None else None
        )
        return PodApplDetailDto(
            id=application_id,
            podId=application_pod_id,
            user=user_dto,
            message=application_message_str,
            status=application_status_str,
            appliedAt=application_applied_at or 0,
            reviewedAt=application_reviewed_at,
            reviewedBy=reviewer_dto,
        )

    # - MARK: 신청서 취소 (application_id 사용)
    async def cancel_application_by_id(self, application_id: int, user_id: int) -> bool:
        logger.info(
            f"신청서 삭제 시도: application_id={application_id}, user_id={user_id}"
        )

        # 신청서 조회
        application = await self._application_repo.get_application_by_id(application_id)

        if not application:
            logger.error(f"신청서를 찾을 수 없음: application_id={application_id}")
            if application.pod_id:
                raise PodNotFoundException(application.pod_id)
            raise PodNotFoundException(0)  # 신청서를 찾을 수 없음

        application_pod_id = application.pod_id or 0
        logger.info(
            f"신청서 정보: id={application.id or 0}, pod_id={application_pod_id}, user_id={application.user_id or 0}, status={application.status or ''}"
        )

        # 본인의 신청서인지 확인
        if application.user_id != user_id:
            logger.error(
                f"권한 없음: 신청서 user_id={application.user_id}, 요청 user_id={user_id}"
            )
            raise NoPodAccessPermissionException(
                application_pod_id, user_id
            )  # 권한 없음

        # pending 상태만 취소 가능
        application_status = application.status or ""
        if application_status != "pending":
            logger.error(f"이미 처리된 신청서: status={application_status}")
            raise PodAlreadyClosedException(application_pod_id)  # 이미 처리된 신청서

        logger.info(f"신청서 삭제 진행: application_id={application_id}")
        # 신청서 삭제
        return await self._application_repo.delete_application(application_id)

    # - MARK: 신청서 숨김 처리 (파티장만 가능)
    async def hide_application_by_owner(
        self, application_id: int, owner_id: int
    ) -> bool:
        """파티장이 신청서를 숨김 처리"""
        logger.info(
            f"신청서 숨김 처리 시도: application_id={application_id}, owner_id={owner_id}"
        )

        # 신청서 조회
        application = await self._application_repo.get_application_by_id(application_id)
        if not application:
            logger.error(f"신청서를 찾을 수 없음: application_id={application_id}")
            raise PodNotFoundException(0)

        # 파티 조회하여 파티장 확인
        if application.pod_id is None:
            raise PodNotFoundException(0)
        if not isinstance(application.pod_id, int):
            raise PodNotFoundException(0)
        application_pod_id = cast(int, application.pod_id)
        pod = await self._pod_repo.get_pod_by_id(application_pod_id)
        if not pod:
            logger.error(f"파티를 찾을 수 없음: pod_id={application_pod_id}")
            raise PodNotFoundException(application_pod_id)

        # 파티장 권한 확인
        if pod.owner_id != owner_id:
            logger.error(
                f"파티장 권한 없음: pod_owner_id={pod.owner_id}, 요청 owner_id={owner_id}"
            )
            raise NoPodAccessPermissionException(application_pod_id, owner_id)

        logger.info(f"신청서 숨김 처리 진행: application_id={application_id}")
        # 신청서 숨김 처리
        return await self._application_repo.hide_application(application_id)

    # - MARK: 사용자 역할에 따른 신청서 처리
    async def handle_application_by_user_role(
        self, application_id: int, user_id: int
    ) -> dict | None:
        """파티장: 숨김 처리, 신청자: 취소 처리"""
        logger.info(
            f"신청서 처리 시도: application_id={application_id}, user_id={user_id}"
        )

        # 신청서 조회
        application = await self._application_repo.get_application_by_id(application_id)
        if not application:
            logger.error(f"신청서를 찾을 수 없음: application_id={application_id}")
            raise PodNotFoundException(0)

        # 파티 조회
        if application.pod_id is None:
            raise PodNotFoundException(0)
        if not isinstance(application.pod_id, int):
            raise PodNotFoundException(0)
        application_pod_id = cast(int, application.pod_id)
        pod = await self._pod_repo.get_pod_by_id(application_pod_id)
        if not pod:
            logger.error(f"파티를 찾을 수 없음: pod_id={application_pod_id}")
            raise PodNotFoundException(application_pod_id)

        # 사용자 역할 확인
        is_owner = pod.owner_id == user_id
        is_applicant = application.user_id == user_id

        if not is_owner and not is_applicant:
            logger.error(
                f"권한 없음: user_id={user_id}, pod_owner_id={pod.owner_id}, applicant_id={application.user_id}"
            )
            raise NoPodAccessPermissionException(application_pod_id, user_id)

        if is_owner:
            # 파티장인 경우: 신청서 숨김 처리
            logger.info(f"파티장이 신청서 숨김 처리: application_id={application_id}")
            success = await self._application_repo.hide_application(application_id)
            return {
                "action": "hidden",
                "success": success,
                "message": "신청서가 성공적으로 숨김 처리되었습니다.",
            }

        elif is_applicant:
            # 신청자인 경우: 신청 취소 (삭제)
            logger.info(f"신청자가 신청 취소: application_id={application_id}")

            # pending 상태만 취소 가능
            application_status = application.status
            if application_status != "pending":
                logger.error(f"이미 처리된 신청서: status={application_status}")
                raise PodAlreadyClosedException(application_pod_id)

            success = await self._application_repo.delete_application(application_id)
            return {
                "action": "cancelled",
                "success": success,
                "message": "신청이 성공적으로 취소되었습니다.",
            }

    # - MARK: 파티 정원 가득 참 알림
    async def _send_capacity_full_notification(self, pod_id: int, pod) -> None:
        """파티 정원이 가득 찬 경우 파티장에게 알림 전송"""
        try:
            if pod.owner_id is None:
                return
            logger.info(
                f"[정원 가득 참 알림] 시작: pod_id={pod_id}, owner_id={pod.owner_id}"
            )

            # 파티장 정보 조회
            owner_result = await self._session.execute(
                select(User).where(User.id == pod.owner_id)
            )
            owner = owner_result.scalar_one_or_none()

            if not owner:
                logger.warning(
                    f"[정원 가득 참 알림] 파티장 정보를 찾을 수 없음: pod_id={pod_id}, owner_id={pod.owner_id}"
                )
                return

            # 파티장에게 알림 전송
            if owner.fcm_token:
                logger.info(
                    f"[정원 가득 참 알림] FCM 전송 시도: owner_id={owner.id}, pod_id={pod_id}, "
                    f"fcm_token={owner.fcm_token[:20] if owner.fcm_token else 'None'}..."
                )
                await self._fcm_service.send_pod_capacity_full(
                    token=owner.fcm_token,
                    party_name=pod.title or "",
                    pod_id=pod_id,
                    db=self._db,
                    user_id=owner.id,
                    related_user_id=pod.owner_id,
                )
                logger.info(
                    f"[정원 가득 참 알림] 전송 성공: owner_id={owner.id}, pod_id={pod_id}"
                )
            else:
                logger.warning(
                    f"[정원 가득 참 알림] 파티장 FCM 토큰이 없음: owner_id={owner.id}, pod_id={pod_id}"
                )

        except Exception as e:
            logger.error(
                f"[정원 가득 참 알림] 처리 중 오류: pod_id={pod_id}, error={e}",
                exc_info=True,
            )

    # - MARK: 새 멤버 참여 알림
    async def _send_new_member_notification(
        self, pod_id: int, new_member_id: int
    ) -> None:
        """새 멤버 참여 시 파티장, 신청자 제외 참여 유저에게 알림 전송"""
        try:
            # 파티 정보 조회
            pod = await self._pod_repo.get_pod_by_id(pod_id)
            if not pod:
                return

            # 신청자 정보 조회
            new_member_result = await self._session.execute(
                select(User).where(User.id == new_member_id)
            )
            new_member = new_member_result.scalar_one_or_none()
            if not new_member:
                return

            # 파티 참여자 목록 조회
            participants = await self._pod_repo.get_pod_participants(pod_id)

            # 파티장, 신청자 제외 참여 유저에게 알림 전송
            new_member_nickname = new_member.nickname or ""
            pod_title = pod.title or ""
            for participant in participants:
                # 파티장 제외
                if (
                    participant.id is not None
                    and pod.owner_id is not None
                    and participant.id == pod.owner_id
                ):
                    continue
                # 신청자 제외
                if participant.id == new_member_id:
                    continue

                try:
                    participant_id = participant.id
                    participant_fcm_token = participant.fcm_token
                    if participant_fcm_token and participant_id:
                        await self._fcm_service.send_pod_new_member(
                            token=participant_fcm_token,
                            nickname=new_member_nickname,
                            party_name=pod_title,
                            pod_id=pod_id,
                            db=self._session,
                            user_id=participant_id,
                            related_user_id=new_member_id,
                        )
                        logger.info(
                            f"새 멤버 참여 알림 전송 성공: user_id={participant_id}, pod_id={pod_id}, new_member_id={new_member_id}"
                        )
                    else:
                        logger.warning(
                            f"FCM 토큰이 없는 사용자: user_id={participant_id}"
                        )

                except Exception as e:
                    participant_id = participant.id if participant else None
                    logger.error(
                        f"새 멤버 참여 알림 전송 실패: user_id={participant_id}, error={e}"
                    )

        except Exception as e:
            logger.error(
                f"새 멤버 참여 알림 처리 중 오류: pod_id={pod_id}, new_member_id={new_member_id}, error={e}"
            )

    # - MARK: 좋아요한 파티에 자리 생김 알림
    async def _send_spot_opened_notifications(self, pod_id: int, pod) -> None:
        """파티에 자리가 생겼을 때 좋아요한 사용자들에게 알림 전송"""
        try:
            if not pod:
                return

            # 해당 파티를 좋아요한 사용자들 조회
            from app.features.pods.models.pod.pod_like import PodLike
            from app.features.users.models import User
            from sqlalchemy import select

            likes_query = (
                select(User)
                .join(PodLike, User.id == PodLike.user_id)
                .where(PodLike.pod_id == pod_id)
                .distinct()
            )

            likes_result = await self._session.execute(likes_query)
            liked_users = likes_result.scalars().all()

            if not liked_users:
                logger.info(f"파티 {pod_id}를 좋아요한 사용자가 없음")
                return

            # 각 좋아요한 사용자에게 알림 전송
            for user in liked_users:
                try:
                    if user.fcm_token:
                        await self._fcm_service.send_saved_pod_spot_opened(
                            token=user.fcm_token,
                            party_name=pod.title or "",
                            pod_id=pod_id,
                            db=self._db,
                            user_id=user.id,
                            related_user_id=pod.owner_id,
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
