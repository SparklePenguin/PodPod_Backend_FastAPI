from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod.pod import PodCRUD
from app.schemas.pod import PodCreateRequest, PodDto
from app.schemas.common import PageDto
from app.utils.file_upload import save_upload_file
from fastapi import UploadFile
from app.models.pod import Pod
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
        image: Optional[UploadFile] = None,
        thumbnail: Optional[UploadFile] = None,
    ) -> Optional[Pod]:
        image_url = None
        thumbnail_url = None

        # 이미지 저장 (썸네일, 이미지)
        if image is not None:
            image_url = await save_upload_file(image, "uploads/pods/images")
        if thumbnail is not None:
            thumbnail_url = await save_upload_file(thumbnail, "uploads/pods/thumbnails")

        # 파티 생성
        return await self.crud.create_pod(
            owner_id=owner_id,
            title=req.title,
            description=req.description,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
            sub_category=req.sub_category,
            capacity=req.capacity,
            place=req.place,
            address=req.address,
            sub_address=req.sub_address,
            meeting_date=req.meetingDate,
            meeting_time=req.meetingTime,
            selected_artist_id=req.selected_artist_id,
        )

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

        # SQLAlchemy 모델을 DTO로 변환
        pod_dtos = [PodDto.model_validate(pod) for pod in pods]

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

        # SQLAlchemy 모델을 DTO로 변환
        pod_dtos = [PodDto.model_validate(pod) for pod in pods]

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

        # SQLAlchemy 모델을 DTO로 변환
        pod_dtos = [PodDto.model_validate(pod) for pod in pods]

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

        # SQLAlchemy 모델을 DTO로 변환
        pod_dtos = [PodDto.model_validate(pod) for pod in pods]

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
