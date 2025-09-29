from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod.pod import PodCRUD
from app.schemas.pod import PodCreateRequest, PodDto
from app.schemas.common import PageDto
from app.utils.file_upload import save_upload_file
from fastapi import UploadFile
from app.models.pod import Pod
from app.models.pod.pod_status import PodStatus
import math


class PodService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodCRUD(db)

    # - MARK: 파티 생성
    async def create_pod(
        self,
        owner_id: int,
        req: PodCreateRequest,
        images: list[UploadFile] = None,
        status: PodStatus = PodStatus.RECRUITING,
    ) -> Optional[PodDto]:
        image_url = None
        thumbnail_url = None

        # 이미지 저장 및 최적화
        if images:
            first_image = images[0]
            image_url = await save_upload_file(first_image, "uploads/pods/images")

            # 첫 번째 이미지에서 썸네일 생성
            try:
                thumbnail_url = await self._create_thumbnail_from_image(first_image)
            except ValueError as e:
                # 썸네일 생성 실패 시 메인 이미지 URL을 썸네일로 사용
                thumbnail_url = image_url

        # 파티 생성 (채팅방 포함)
        pod = await self.crud.create_pod_with_chat(
            owner_id=owner_id,
            title=req.title,
            description=req.description,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            sub_categories=req.sub_categories,
            capacity=req.capacity,
            place=req.place,
            address=req.address,
            sub_address=req.sub_address,
            meeting_date=req.meetingDate,
            meeting_time=req.meetingTime,
            selected_artist_id=req.selected_artist_id,
            status=status,
        )

        # Pod 모델을 PodDto로 변환 (다른 조회 API들과 동일한 방식)
        if pod:
            pod_dto = PodDto.model_validate(pod)
            # 통계 필드 설정 (다른 조회 API들과 동일한 방식)
            pod_dto.joined_users_count = await self.crud.get_joined_users_count(pod.id)
            pod_dto.like_count = await self.crud.get_like_count(pod.id)
            pod_dto.view_count = await self.crud.get_view_count(pod.id)
            pod_dto.is_liked = await self.crud.is_liked_by_user(pod.id, owner_id)
            return pod_dto
        return None

    async def _create_thumbnail_from_image(self, image: UploadFile) -> str:
        """이미지에서 썸네일을 생성하여 저장"""
        from PIL import Image
        import io
        import uuid
        import os

        # 이미지 읽기
        image_content = await image.read()

        # 이미지 파일 검증
        if not image_content:
            raise ValueError("이미지 파일이 비어있습니다")

        try:
            img = Image.open(io.BytesIO(image_content))
        except Exception as e:
            raise ValueError(f"이미지 파일을 읽을 수 없습니다: {str(e)}")

        # 썸네일 크기 (300x300)
        thumbnail_size = (300, 300)

        # 썸네일 생성 (비율 유지하며 리사이즈)
        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # 썸네일 저장
        thumbnail_filename = f"{uuid.uuid4()}.jpg"
        thumbnail_path = f"uploads/pods/thumbnails/{thumbnail_filename}"

        # 디렉토리 생성
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

        # RGB로 변환 (JPEG 저장을 위해)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 썸네일 저장
        img.save(thumbnail_path, "JPEG", quality=85, optimize=True)

        return thumbnail_path

    # - MARK: 파티 상세 조회
    async def get_pod_detail(self, pod_id: int) -> Optional[Pod]:
        return await self.crud.get_pod_by_id(pod_id)

    # - MARK: 파티 수정
    async def update_pod(self, pod_id: int, **fields) -> Optional[Pod]:
        return await self.crud.update_pod(pod_id, **fields)

    # - MARK: 파티 삭제
    async def delete_pod(self, pod_id: int) -> None:
        return await self.crud.delete_pod(pod_id)

    # - MARK: 요즘 인기 있는 파티 조회
    async def get_trending_pods(
        self, user_id: int, selected_artist_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """
        요즘 인기 있는 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 7일 이내 인기도 기반 정렬
        - 페이지네이션 지원
        """
        pods = await self.crud.get_trending_pods(
            user_id, selected_artist_id, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = PodDto.model_validate(pod)
            # 참여자 수 계산
            joined_count = await self.crud.get_joined_users_count(pod.id)
            pod_dto.joined_users_count = joined_count
            # 좋아요 수 계산
            like_count = await self.crud.get_like_count(pod.id)
            pod_dto.like_count = like_count
            pod_dtos.append(pod_dto)

        # TODO: 실제 total_count를 가져오는 로직 추가 필요
        total_count = len(pod_dtos)  # 임시로 현재 페이지 아이템 수 사용
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    # - MARK: 마감 직전 파티 조회
    async def get_closing_soon_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """
        마감 직전 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 에디터가 설정한 지역 (선택사항)
        - 24시간 이내 마감 모임 우선 정렬
        - 페이지네이션 지원
        """
        pods = await self.crud.get_closing_soon_pods(
            user_id, selected_artist_id, location, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = PodDto.model_validate(pod)
            # 참여자 수 계산
            joined_count = await self.crud.get_joined_users_count(pod.id)
            pod_dto.joined_users_count = joined_count
            # 좋아요 수 계산
            like_count = await self.crud.get_like_count(pod.id)
            pod_dto.like_count = like_count
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    # - MARK: 우리 만난적 있어요 파티 조회
    async def get_history_based_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """
        우리 만난적 있어요 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 이전 매칭 사용자 기반 추천
        - 페이지네이션 지원
        """
        pods = await self.crud.get_history_based_pods(
            user_id, selected_artist_id, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = PodDto.model_validate(pod)
            # 참여자 수 계산
            joined_count = await self.crud.get_joined_users_count(pod.id)
            pod_dto.joined_users_count = joined_count
            # 좋아요 수 계산
            like_count = await self.crud.get_like_count(pod.id)
            pod_dto.like_count = like_count
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    # - MARK: 인기 최고 카테고리 파티 조회
    async def get_popular_categories_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDto]:
        """
        인기 최고 카테고리 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 일주일 기준 인기 카테고리 기반 추천
        - 페이지네이션 지원
        """
        pods = await self.crud.get_popular_categories_pods(
            user_id, selected_artist_id, location, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = PodDto.model_validate(pod)
            # 참여자 수 계산
            joined_count = await self.crud.get_joined_users_count(pod.id)
            pod_dto.joined_users_count = joined_count
            # 좋아요 수 계산
            like_count = await self.crud.get_like_count(pod.id)
            pod_dto.like_count = like_count
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    # - MARK: 특정 유저가 개설한 파티 목록 조회
    async def get_user_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """특정 유저가 개설한 파티 목록 조회"""
        pods, total_count = await self.crud.get_user_pods(user_id, page, size)

        pod_dtos = []
        for pod in pods:
            # 각 파티의 참여자 수와 좋아요 수 계산
            joined_users_count = await self.crud.get_joined_users_count(pod.id)
            like_count = await self.crud.get_like_count(pod.id)

            pod_dto = PodDto.model_validate(pod)
            pod_dto.joined_users_count = joined_users_count
            pod_dto.like_count = like_count

            pod_dtos.append(pod_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            page_size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    # - MARK: 파티 좋아요 관련 메서드
    async def like_pod(self, pod_id: int, user_id: int) -> bool:
        """파티 좋아요"""
        from app.crud.pod.pod_like import PodLikeCRUD

        like_crud = PodLikeCRUD(self.db)
        return await like_crud.like_pod(pod_id, user_id)

    async def unlike_pod(self, pod_id: int, user_id: int) -> bool:
        """파티 좋아요 취소"""
        from app.crud.pod.pod_like import PodLikeCRUD

        like_crud = PodLikeCRUD(self.db)
        return await like_crud.unlike_pod(pod_id, user_id)

    async def like_status(self, pod_id: int, user_id: int) -> dict:
        """파티 좋아요 상태 조회"""
        from app.crud.pod.pod_like import PodLikeCRUD

        like_crud = PodLikeCRUD(self.db)

        is_liked = await like_crud.is_liked(pod_id, user_id)
        like_count = await like_crud.like_count(pod_id)

        return {"liked": is_liked, "count": like_count}
