"""Pod Use Case - 비즈니스 로직 처리"""

import json
from typing import List

from app.common.schemas import PageDto
from app.features.follow.use_cases.follow_use_case import FollowUseCase
from app.features.pods.exceptions import (
    InvalidDateException,
    InvalidPodStatusException,
    InvalidPodTypeException,
    MissingStatusException,
    NoPodAccessPermissionException,
    PodNotFoundException,
    SelectedArtistIdRequiredException,
)
from app.features.pods.models import (
    AccompanySubCategory,
    EtcSubCategory,
    GoodsSubCategory,
    PodStatus,
    TourSubCategory,
)
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.schemas import PodDetailDto, PodDto, PodForm, PodSearchRequest
from app.features.pods.services.pod_notification_service import PodNotificationService
from app.features.pods.services.pod_service import PodService
from app.features.users.exceptions import UserNotFoundException
from app.features.users.repositories import UserRepository
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession


class PodUseCase:
    """Pod 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        pod_service: PodService,
        pod_repo: PodRepository,
        notification_service: PodNotificationService,
        follow_use_case: FollowUseCase,
        user_repo: UserRepository,
    ):
        self._session = session
        self._pod_service = pod_service
        self._pod_repo = pod_repo
        self._notification_service = notification_service
        self._follow_use_case = follow_use_case
        self._user_repo = user_repo

    # MARK: - 파티 생성
    async def create_pod_from_form(
        self,
        owner_id: int,
        pod_form: PodForm,
        images: list[UploadFile],
        status: PodStatus = PodStatus.RECRUITING,
    ) -> PodDetailDto:
        """Form 데이터로부터 파티 생성 (비즈니스 로직 검증)"""
        # sub_categories 파싱 및 변환
        pod_form.sub_categories = self._parse_sub_categories(pod_form.sub_categories)

        # 필수 필드 검증
        self._validate_for_create(pod_form)

        # sub_categories 검증 및 필터링 (use case에서 처리)
        if pod_form.sub_categories:
            sub_categories_list = self._get_sub_categories_list(pod_form.sub_categories)
            if sub_categories_list:
                validated_categories = self._validate_and_filter_categories(
                    sub_categories_list
                )
                # 검증된 카테고리로 업데이트
                pod_form.sub_categories = json.dumps(validated_categories)

        # 서비스 로직 호출
        try:
            result = await self._pod_service.create_pod_from_form(
                owner_id=owner_id,
                pod_form=pod_form,
                images=images,
                status=status,
            )

            # 팔로워들에게 파티 생성 알림 전송
            if result and result.id:
                try:
                    await self._follow_use_case.send_followed_user_pod_created_notification(
                        owner_id, result.id
                    )
                except Exception:
                    # 알림 전송 실패는 무시하고 계속 진행
                    pass

            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 수정
    async def update_pod_from_form(
        self,
        pod_id: int,
        current_user_id: int,
        pod_form: PodForm,
        new_images: list[UploadFile | None] = None,
    ) -> PodDetailDto:
        """Form 데이터로부터 파티 수정 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티 소유자 확인
        if pod.owner_id != current_user_id:
            raise NoPodAccessPermissionException(pod_id, current_user_id)

        # sub_categories 파싱 및 변환
        pod_form.sub_categories = self._parse_sub_categories(pod_form.sub_categories)

        # sub_categories 검증 및 필터링 (제공된 경우에만, use case에서 처리)
        if pod_form.sub_categories:
            sub_categories_list = self._get_sub_categories_list(pod_form.sub_categories)
            if sub_categories_list:
                validated_categories = self._validate_and_filter_categories(
                    sub_categories_list
                )
                # 검증된 카테고리로 업데이트
                pod_form.sub_categories = json.dumps(validated_categories)

        # 서비스 로직 호출
        try:
            result = await self._pod_service.update_pod_from_form(
                pod_id=pod_id,
                current_user_id=current_user_id,
                pod_form=pod_form,
                new_images=new_images,
            )

            # 알림 전송
            if result:
                updated_pod = await self._pod_repo.get_pod_by_id(pod_id)
                if updated_pod:
                    await self._notification_service.send_pod_update_notification(
                        pod_id, updated_pod
                    )

            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 상태 업데이트
    async def update_pod_status_by_owner(
        self, pod_id: int, status_value: str | None, user_id: int
    ) -> PodDetailDto:
        """파티장이 파티 상태를 변경 (비즈니스 로직 검증)"""
        # status 필드 검증
        if status_value is None:
            raise MissingStatusException()

        # 상태 값 검증
        try:
            status = PodStatus(status_value.upper())
        except ValueError:
            raise InvalidPodStatusException(status_value)

        # 파티 조회
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티장 권한 확인
        if pod.owner_id is None or pod.owner_id != user_id:
            raise NoPodAccessPermissionException(pod_id, user_id)

        # 이미 같은 상태인지 확인
        if pod.status == status:
            return await self._pod_service._convert_pod_to_dto(pod, user_id)

        # 서비스 로직 호출
        try:
            result = await self._pod_service.update_pod_status_by_owner(
                pod_id, status, user_id
            )

            # 알림 전송
            updated_pod = await self._pod_repo.get_pod_by_id(pod_id)
            if updated_pod:
                await self._notification_service.send_pod_status_update_notification(
                    pod_id, updated_pod, status
                )

            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 삭제
    async def delete_pod(self, pod_id: int, current_user_id: int) -> None:
        """파티 삭제 (비즈니스 로직 검증)"""
        # 파티 조회
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티장 권한 확인
        if pod.owner_id != current_user_id:
            raise NoPodAccessPermissionException(pod_id, current_user_id)

        # 서비스 로직 호출
        try:
            await self._pod_service.delete_pod(pod_id)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 나가기
    async def leave_pod(
        self, pod_id: int, user_id: str | None, current_user_id: int
    ) -> dict:
        """파티 나가기 (비즈니스 로직 검증)"""
        from app.features.pods.exceptions import PodAccessDeniedException

        # user_id 파싱
        if user_id is not None and user_id.strip() != "":
            try:
                target_user_id = int(user_id)
            except ValueError:
                target_user_id = current_user_id
        else:
            target_user_id = current_user_id

        # 파티 조회
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티장인지 확인
        if pod.owner_id == target_user_id:
            raise PodAccessDeniedException(
                "파티장은 파티 삭제 엔드포인트를 사용해주세요."
            )

        # 파티장이 아닌 경우 멤버인지 확인
        is_member = await self._pod_repo.is_pod_member(pod_id, target_user_id)
        if not is_member:
            raise NoPodAccessPermissionException(pod_id, target_user_id)

        # 서비스 로직 호출
        try:
            result = await self._pod_service.leave_pod(pod_id, user_id, current_user_id)
            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 상세 조회
    async def get_pod_detail(
        self, pod_id: int, user_id: int | None = None
    ) -> PodDetailDto:
        """파티 상세 조회 (비즈니스 로직 검증)"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 서비스 로직 호출
        return await self._pod_service.get_pod_detail(pod_id, user_id)

    # MARK: - 사용자가 개설한 파티 목록 조회
    async def get_user_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 개설한 파티 목록 조회 (비즈니스 로직 검증)"""

        # 사용자 존재 확인
        user = await self._user_repo.get_by_id(user_id)
        if not user or user.is_del:
            raise UserNotFoundException(user_id)

        # 서비스 로직 호출 (목록 조회는 applications, reviews 제외)
        return await self._pod_service.get_user_pods(
            user_id, page, size, include_applications=False, include_reviews=False
        )

    # MARK: - 파티 목록 조회 (타입별)
    async def get_pods_by_type(
        self,
        user_id: int,
        pod_type: str,
        selected_artist_id: int | None = None,
        location: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[PageDto[PodDto], str, str]:
        """파티 목록 조회 (비즈니스 로직 검증)

        Returns:
            tuple[PageDto[PodDetailDto], message_ko, message_en]: 파티 목록과 메시지
        """
        # 전체 파티 목록 타입들 (selected_artist_id 필수)
        if pod_type == "trending":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self._pod_service.get_trending_pods(
                user_id, selected_artist_id, page, size
            )
            return (
                pods,
                "인기 파티 목록을 조회했습니다.",
                "Successfully retrieved trending pods.",
            )

        elif pod_type == "closing-soon":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self._pod_service.get_closing_soon_pods(
                user_id, selected_artist_id, location, page, size
            )
            return (
                pods,
                "마감 직전 파티 목록을 조회했습니다.",
                "Successfully retrieved closing soon pods.",
            )

        elif pod_type == "history-based":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self._pod_service.get_history_based_pods(
                user_id, selected_artist_id, page, size
            )
            return (
                pods,
                "우리 만난적 있어요 파티 목록을 조회했습니다.",
                "Successfully retrieved history-based pods.",
            )

        elif pod_type == "popular-category":
            if selected_artist_id is None:
                raise SelectedArtistIdRequiredException(pod_type)
            pods = await self._pod_service.get_popular_categories_pods(
                user_id, selected_artist_id, location, page, size
            )
            return (
                pods,
                "인기 카테고리 파티 목록을 조회했습니다.",
                "Successfully retrieved popular category pods.",
            )

        # 사용자별 파티 목록 타입들
        elif pod_type == "joined":
            pods = await self._pod_service.get_user_joined_pods(user_id, page, size)
            return (
                pods,
                "내가 참여한 파티 목록을 조회했습니다.",
                "Successfully retrieved my joined pods.",
            )

        elif pod_type == "liked":
            pods = await self._pod_service.get_user_liked_pods(user_id, page, size)
            return (
                pods,
                "내가 저장한 파티 목록을 조회했습니다.",
                "Successfully retrieved my liked pods.",
            )

        elif pod_type == "owned":
            pods = await self._pod_service.get_user_pods(user_id, page, size)
            return (
                pods,
                "내가 개설한 파티 목록을 조회했습니다.",
                "Successfully retrieved my owned pods.",
            )

        elif pod_type == "following":
            pods = await self._follow_use_case.get_following_pods(
                user_id=user_id, page=page, size=size
            )
            return (
                pods,
                "팔로우하는 사용자의 파티 목록을 조회했습니다.",
                "Successfully retrieved following users' pods.",
            )

        else:
            raise InvalidPodTypeException(pod_type)

    # MARK: - 파티 검색
    async def search_pods(
        self,
        user_id: int | None,
        search_request: PodSearchRequest,
    ) -> PageDto[PodDto]:
        """파티 검색 (비즈니스 로직 검증)"""

        # 날짜 검증
        if (
            search_request.start_date
            and search_request.end_date
            and search_request.start_date > search_request.end_date
        ):
            raise InvalidDateException("시작 날짜가 종료 날짜보다 늦습니다.")

        # 서비스 로직 호출
        return await self._pod_service.search_pods(
            user_id=user_id,
            title=search_request.title,
            main_category=search_request.main_category,
            sub_category=search_request.sub_category,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            location=search_request.location,
            page=search_request.page or 1,
            size=search_request.size or 20,
        )

    # MARK: - 헬퍼 메서드
    def _validate_for_create(self, pod_form) -> None:
        """생성 시 필수 필드 검증"""
        required_fields = {
            "title": pod_form.title,
            "sub_categories": pod_form.sub_categories,
            "capacity": pod_form.capacity,
            "place": pod_form.place,
            "address": pod_form.address,
            "meeting_date": pod_form.meeting_date,
            "selected_artist_id": pod_form.selected_artist_id,
        }

        missing_fields = [
            field for field, value in required_fields.items() if value is None
        ]

        if missing_fields:
            raise ValueError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")

        # sub_categories가 빈 배열이면 안됨
        sub_categories_list = self._get_sub_categories_list(pod_form.sub_categories)
        if not sub_categories_list or sub_categories_list == []:
            raise ValueError("서브 카테고리는 필수입니다")

    def _get_sub_categories_list(self, sub_categories: str | None) -> list[str] | None:
        """sub_categories를 JSON 문자열에서 리스트로 변환 (Optional)"""
        if sub_categories is None:
            return None
        try:
            parsed = json.loads(sub_categories)
            return parsed if isinstance(parsed, list) else None
        except Exception:
            return None

    def _parse_sub_categories(self, v) -> str | None:
        """sub_categories를 문자열로 변환 (리스트면 JSON 문자열로)"""
        if v is None:
            return None
        if isinstance(v, str):
            # JSON 형식 검증
            try:
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    return None
                if parsed == []:
                    return None
                return v
            except (json.JSONDecodeError, ValueError):
                return None
        elif isinstance(v, list):
            if not v:
                return None
            return json.dumps(v)
        return None

    # MARK: - 카테고리 검증 및 필터링 (비즈니스 로직)
    def _validate_and_filter_categories(self, categories: List[str]) -> List[str]:
        """서브 카테고리 검증 및 필터링 (유효하지 않은 카테고리는 필터링하고 경고 출력)"""
        if not categories:
            return []

        # 모든 유효한 카테고리 키들을 수집
        valid_categories = set()
        valid_categories.update([cat.name for cat in AccompanySubCategory])
        valid_categories.update([cat.name for cat in GoodsSubCategory])
        valid_categories.update([cat.name for cat in TourSubCategory])
        valid_categories.update([cat.name for cat in EtcSubCategory])

        # 유효한 카테고리만 필터링
        valid_sub_categories = [cat for cat in categories if cat in valid_categories]

        # 유효하지 않은 카테고리가 있으면 로그만 남기고 필터링된 결과 반환
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            # 카테고리를 그룹별로 정리
            goods_categories = [cat.name for cat in GoodsSubCategory]
            accompany_categories = [cat.name for cat in AccompanySubCategory]
            tour_categories = [cat.name for cat in TourSubCategory]
            etc_categories = [cat.name for cat in EtcSubCategory]

            print(
                f"""⚠️ 유효하지 않은 카테고리가 필터링되었습니다: {", ".join(invalid_categories)}

사용 가능한 카테고리:
📦 굿즈: {", ".join(goods_categories)}
👥 동행: {", ".join(accompany_categories)}
🗺️ 투어: {", ".join(tour_categories)}
📋 기타: {", ".join(etc_categories)}"""
            )

        return valid_sub_categories
