from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod.pod import PodCRUD
from app.crud.pod.recruitment import RecruitmentCRUD
from app.crud.pod.pod_application import PodApplicationCRUD
from app.core.error_codes import raise_error
from app.schemas.pod.pod_application_dto import PodApplicationDto
from app.schemas.follow import SimpleUserDto
from app.models.user import User


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

        # 이미 멤버인지 확인
        already_member = any(m.user_id == user_id for m in pod.members)
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

        # PodApplicationDto로 변환하여 반환
        return PodApplicationDto(
            id=application.id,
            podId=application.pod_id,
            user=SimpleUserDto.model_validate(user),
            message=application.message,
            status=application.status,
            appliedAt=application.applied_at,
            reviewedAt=application.reviewed_at,
            reviewedBy=(
                SimpleUserDto.model_validate(application.reviewer)
                if application.reviewer
                else None
            ),
        )

    # - MARK: 신청서 승인/거절
    async def review_application(
        self, application_id: int, status: str, reviewed_by: int
    ) -> PodApplicationDto:
        # 신청서 승인/거절 처리
        application = await self.application_crud.review_application(
            application_id, status, reviewed_by
        )

        # 승인된 경우 멤버로 추가
        if status == "approved":
            await self.crud.add_member(
                application.pod_id,
                application.user_id,
                role="member",
                message=application.message,
            )

        # User 정보 가져오기
        user = await self.db.get(User, application.user_id)
        reviewer = (
            await self.db.get(User, reviewed_by) if application.reviewer else None
        )

        # PodApplicationDto로 변환하여 반환
        return PodApplicationDto(
            id=application.id,
            podId=application.pod_id,
            user=SimpleUserDto.model_validate(user),
            message=application.message,
            status=application.status,
            appliedAt=application.applied_at,
            reviewedAt=application.reviewed_at,
            reviewedBy=SimpleUserDto.model_validate(reviewer) if reviewer else None,
        )

    # - MARK: 신청서 취소
    async def cancel_application(self, pod_id: int, user_id: int) -> bool:
        # 해당 파티에 대한 사용자의 신청서 찾기
        applications = await self.application_crud.get_applications_by_user_id(user_id)
        target_application = None

        for app in applications:
            if app.pod_id == pod_id and app.status == "pending":
                target_application = app
                break

        if not target_application:
            raise_error("APPLICATION_NOT_FOUND")

        # 신청서 삭제
        return await self.application_crud.delete_application(target_application.id)
