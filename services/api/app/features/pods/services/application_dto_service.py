"""Application DTO 변환 서비스

신청서 모델을 DTO로 변환하는 단일 책임을 가진 서비스입니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.pods.schemas.application_schemas import PodApplDto
from app.features.pods.models.application_models import Application
from app.features.users.schemas.user_schemas import UserDto
from app.features.users.repositories.user_repository import UserRepository
from app.features.users.services.user_dto_service import UserDtoService


class ApplicationDtoService:
    """Application DTO 변환을 담당하는 서비스"""

    def __init__(self, session: AsyncSession, user_repo: UserRepository):
        self._session = session
        self._user_repo = user_repo

    async def convert_to_dto(
        self,
        application: Application,
        reviewer_dto: UserDto | None = None,
    ) -> PodApplDto:
        """Application 모델을 PodApplDto로 변환"""
        user_id = application.user_id or 0
        user = await self._user_repo.get_by_id(user_id)
        tendency_type = await self._user_repo.get_user_tendency_type(user_id)
        user_dto = UserDtoService.create_user_dto(user, tendency_type)

        return PodApplDto(
            id=application.id or 0,
            pod_id=application.pod_id or 0,
            user=user_dto,
            message=application.message,
            status=str(application.status.name) if application.status else "",
            applied_at=application.applied_at,
            reviewed_at=application.reviewed_at,
            reviewed_by=reviewer_dto,
        )

    async def convert_to_list_dto(
        self,
        application: Application,
        include_message: bool = False,
    ) -> PodApplDto:
        """Application 모델을 리스트용 PodApplDto로 변환 (간단한 정보만)"""
        user_id = application.user_id or 0
        user = await self._user_repo.get_by_id(user_id)
        tendency_type = await self._user_repo.get_user_tendency_type(user_id)
        user_dto = UserDtoService.create_user_dto(user, tendency_type or "")

        message = None
        if include_message:
            message = getattr(application, "message", None)

        status_str = str(application.status.name) if application.status else ""

        return PodApplDto(
            id=application.id or 0,
            pod_id=application.pod_id or 0,
            user=user_dto,
            status=status_str,
            message=message,
            applied_at=application.applied_at,
        )

    async def create_reviewer_dto(self, reviewer_id: int) -> UserDto | None:
        """리뷰어 UserDto 생성"""
        if not reviewer_id:
            return None

        reviewer = await self._user_repo.get_by_id(reviewer_id)
        if not reviewer or reviewer.id is None:
            return None

        tendency_type = await self._user_repo.get_user_tendency_type(reviewer_id)
        return UserDtoService.create_user_dto(reviewer, tendency_type)
