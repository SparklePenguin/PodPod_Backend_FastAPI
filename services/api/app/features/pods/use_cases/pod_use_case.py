"""Pod Use Case - 비즈니스 로직 처리"""

import json
from datetime import date, time, timezone
from pathlib import Path

from app.core.config import settings
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.follow.use_cases.follow_use_case import FollowUseCase
from app.features.pods.exceptions import (
    InvalidDateException,
    InvalidPodStatusException,
    MissingStatusException,
    NoPodAccessPermissionException,
    PodAccessDeniedException,
    PodNotFoundException,
    PodUpdateFailedException,
)
from app.features.pods.models import PodStatus
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.schemas import ImageOrderDto, PodDetailDto, PodForm
from app.features.pods.services.pod_category_service import PodCategoryService
from app.features.pods.services.pod_enrichment_service import PodEnrichmentService
from app.features.pods.services.pod_image_service import PodImageService
from app.features.pods.services.pod_notification_service import PodNotificationService
from app.features.pods.services.pod_validation_service import PodValidationService
from app.utils.file_upload import save_upload_file
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession


class PodUseCase:
    """Pod 관련 비즈니스 로직을 처리하는 Use Case"""

    def __init__(
        self,
        session: AsyncSession,
        pod_repo: PodRepository,
        enrichment_service: PodEnrichmentService,
        notification_service: PodNotificationService,
        follow_use_case: FollowUseCase,
    ):
        self._session = session
        self._pod_repo = pod_repo
        self._enrichment_service = enrichment_service
        self._notification_service = notification_service
        self._follow_use_case = follow_use_case
        # 서비스 초기화
        self._image_service = PodImageService(pod_repo)

    # MARK: - 파티 생성
    async def create_pod_from_form(
        self,
        owner_id: int,
        pod_form: PodForm,
        images: list[UploadFile],
        status: PodStatus = PodStatus.RECRUITING,
    ) -> PodDetailDto:
        """Form 데이터로부터 파티 생성"""
        # sub_categories 파싱 및 변환
        pod_form.sub_categories = PodCategoryService.parse_to_string(
            pod_form.sub_categories
        )

        # 필수 필드 검증
        PodValidationService.validate_for_create(pod_form)

        # sub_categories 검증 및 필터링
        sub_categories_list: list[str] = []
        if pod_form.sub_categories:
            sub_categories_list = PodCategoryService.parse_to_list(
                pod_form.sub_categories
            )
            if sub_categories_list:
                validated_categories = PodCategoryService.validate_and_filter(
                    sub_categories_list
                )
                sub_categories_list = validated_categories

        # meetingDate(datetime) → date/time 분리
        if not pod_form.meeting_date:
            raise InvalidDateException("meetingDate 필드가 누락되었습니다.")

        try:
            dt = pod_form.meeting_date
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            parsed_meeting_date: date = dt_utc.date()
            parsed_meeting_time: time = dt_utc.time()
        except (ValueError, AttributeError) as e:
            raise InvalidDateException(str(pod_form.meeting_date)) from e

        try:
            result = await self._create_pod(
                owner_id=owner_id,
                title=pod_form.title or "",
                description=pod_form.description,
                sub_categories=sub_categories_list,
                capacity=pod_form.capacity or 0,
                place=pod_form.place or "",
                address=pod_form.address or "",
                sub_address=pod_form.sub_address,
                x=pod_form.x,
                y=pod_form.y,
                meeting_date=parsed_meeting_date,
                meeting_time=parsed_meeting_time,
                selected_artist_id=pod_form.selected_artist_id or 0,
                images=images,
                status=status,
            )

            if result is None:
                raise PodUpdateFailedException(0)

            # 팔로워들에게 파티 생성 알림 전송
            if result.id:
                try:
                    await self._follow_use_case.send_followed_user_pod_created_notification(
                        owner_id, result.id
                    )
                except Exception:
                    pass

            await self._session.commit()
            return result
        except Exception:
            await self._session.rollback()
            raise

    async def _create_pod(
        self,
        owner_id: int,
        title: str,
        description: str | None,
        sub_categories: list[str] | None,
        capacity: int,
        place: str,
        address: str,
        sub_address: str | None,
        x: float | None,
        y: float | None,
        meeting_date: date,
        meeting_time: time,
        selected_artist_id: int,
        images: list[UploadFile | None] | None = None,
        status: PodStatus = PodStatus.RECRUITING,
    ) -> PodDetailDto | None:
        """파티 생성 내부 로직"""
        thumbnail_url = None

        # 첫 번째 이미지로 thumbnail_url 생성
        if images:
            first_image = images[0]
            try:
                thumbnail_url = await self._image_service.create_thumbnail_from_image(
                    first_image
                )
            except ValueError:
                pods_images_dir = Path(settings.UPLOADS_DIR) / "pods" / "images"
                thumbnail_url = await save_upload_file(
                    first_image, str(pods_images_dir)
                )

        # 파티 생성 (채팅방 포함)
        pod = await self._pod_repo.create_pod_with_chat(
            owner_id=owner_id,
            title=title,
            description=description,
            image_url=None,
            thumbnail_url=thumbnail_url,
            sub_categories=sub_categories,
            capacity=capacity,
            place=place,
            address=address,
            sub_address=sub_address,
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            selected_artist_id=selected_artist_id,
            x=x,
            y=y,
            status=status,
        )

        if not pod:
            raise PodNotFoundException(0)

        # 여러 이미지 저장
        if images:
            pods_images_dir = Path(settings.UPLOADS_DIR) / "pods" / "images"
            for index, image in enumerate(images):
                image_url = await save_upload_file(image, str(pods_images_dir))

                # 각 이미지의 썸네일 생성
                image_thumbnail_url = None
                try:
                    image_thumbnail_url = (
                        await self._image_service.create_thumbnail_from_image(image)
                    )
                except ValueError:
                    image_thumbnail_url = image_url

                # PodImage 저장
                await self._pod_repo.add_pod_image(
                    pod_id=pod.id,
                    image_url=image_url,
                    thumbnail_url=image_thumbnail_url,
                    display_order=index,
                )

        # Pod 모델을 PodDetailDto로 변환
        if pod:
            await self._session.refresh(
                pod, ["detail", "images", "applications", "reviews"]
            )
            return await self._enrichment_service.enrich(pod, owner_id)
        return None

    # MARK: - 파티 수정
    async def update_pod_from_form(
        self,
        pod_id: int,
        current_user_id: int,
        pod_form: PodForm,
        new_images: list[UploadFile | None] | None = None,
    ) -> PodDetailDto:
        """Form 데이터로부터 파티 수정"""
        # 파티 존재 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티 소유자 확인
        if pod.owner_id != current_user_id:
            raise NoPodAccessPermissionException(pod_id, current_user_id)

        # sub_categories 파싱 및 변환
        pod_form.sub_categories = PodCategoryService.parse_to_string(
            pod_form.sub_categories
        )

        # sub_categories 검증 및 필터링
        if pod_form.sub_categories:
            sub_categories_list = PodCategoryService.parse_to_list(
                pod_form.sub_categories
            )
            if sub_categories_list:
                validated_categories = PodCategoryService.validate_and_filter(
                    sub_categories_list
                )
                pod_form.sub_categories = json.dumps(validated_categories)

        # 업데이트할 필드들 준비
        pod_update_fields: dict = {}
        pod_detail_update_fields: dict = {}

        if pod_form.title is not None:
            pod_update_fields["title"] = pod_form.title
        if pod_form.description is not None:
            pod_detail_update_fields["description"] = pod_form.description
        if pod_form.sub_categories is not None:
            try:
                parsed = json.loads(pod_form.sub_categories)
                if isinstance(parsed, list):
                    pod_update_fields["sub_categories"] = parsed
            except Exception:
                pass
        if pod_form.capacity is not None:
            pod_update_fields["capacity"] = pod_form.capacity
        if pod_form.place is not None:
            pod_update_fields["place"] = pod_form.place
        if pod_form.address is not None:
            pod_detail_update_fields["address"] = pod_form.address
        if pod_form.sub_address is not None:
            pod_detail_update_fields["sub_address"] = pod_form.sub_address
        if pod_form.x is not None:
            pod_detail_update_fields["x"] = pod_form.x
        if pod_form.y is not None:
            pod_detail_update_fields["y"] = pod_form.y
        if pod_form.selected_artist_id is not None:
            pod_update_fields["selected_artist_id"] = pod_form.selected_artist_id

        # 날짜와 시간 파싱
        if pod_form.meeting_date is not None:
            try:
                dt = pod_form.meeting_date
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_utc = dt.astimezone(timezone.utc)
                pod_update_fields["meeting_date"] = dt_utc.date()
                pod_update_fields["meeting_time"] = dt_utc.time()
            except (ValueError, AttributeError) as e:
                raise InvalidDateException(str(pod_form.meeting_date)) from e

        try:
            result = await self._update_pod_with_images(
                pod_id=pod_id,
                current_user_id=current_user_id,
                update_fields=pod_update_fields,
                pod_detail_update_fields=pod_detail_update_fields,
                image_orders=pod_form.image_orders,
                new_images=new_images,
            )

            if result is None:
                raise PodUpdateFailedException(pod_id)

            # 알림 전송
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

    async def _update_pod_with_images(
        self,
        pod_id: int,
        current_user_id: int,
        update_fields: dict,
        pod_detail_update_fields: dict | None = None,
        image_orders: str | None = None,
        new_images: list[UploadFile | None] | None = None,
    ) -> PodDetailDto | None:
        """파티 수정 내부 로직 (이미지 관리 포함)"""
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            return None

        if pod.owner_id != current_user_id:
            raise PodAccessDeniedException(pod_id, current_user_id)

        # 이미지 순서 처리
        if image_orders is not None and image_orders.strip():
            try:
                order_data = json.loads(image_orders)
                image_order_objects = [
                    ImageOrderDto.model_validate(item) for item in order_data
                ]

                # 기존 이미지 모두 삭제
                await self._image_service.delete_pod_images(pod_id)

                # 새 이미지들을 딕셔너리로 매핑
                new_images_dict: dict = {}
                if new_images:
                    for i, img in enumerate(new_images):
                        new_images_dict[i] = img

                thumbnail_url = None

                # 순서대로 이미지 처리
                for index, order_item in enumerate(image_order_objects):
                    if order_item.type == "existing":
                        if order_item.url:
                            await self._pod_repo.add_pod_image(
                                pod_id=pod_id,
                                image_url=order_item.url,
                                thumbnail_url=order_item.url,
                                display_order=index,
                            )
                            if index == 0:
                                thumbnail_url = order_item.url

                    elif order_item.type == "new":
                        if (
                            order_item.file_index is not None
                            and order_item.file_index in new_images_dict
                        ):
                            image = new_images_dict[order_item.file_index]
                            pods_images_dir = (
                                Path(settings.UPLOADS_DIR) / "pods" / "images"
                            )
                            image_url = await save_upload_file(
                                image, str(pods_images_dir)
                            )

                            image_thumbnail_url = None
                            try:
                                image_thumbnail_url = await self._image_service.create_thumbnail_from_image(
                                    image
                                )
                            except ValueError:
                                image_thumbnail_url = image_url

                            await self._pod_repo.add_pod_image(
                                pod_id=pod_id,
                                image_url=image_url,
                                thumbnail_url=image_thumbnail_url,
                                display_order=index,
                            )

                            if index == 0:
                                thumbnail_url = image_thumbnail_url

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "BAD_REQUEST",
                        "code": 4000,
                        "message": "이미지 순서 데이터가 올바르지 않습니다.",
                    },
                ) from e

            if thumbnail_url:
                update_fields["thumbnail_url"] = thumbnail_url

        # 새 이미지만 있는 경우 (image_orders 없이)
        elif new_images:
            await self._image_service.delete_pod_images(pod_id)
            thumbnail_url = None

            for index, image in enumerate(new_images):
                pods_images_dir = Path(settings.UPLOADS_DIR) / "pods" / "images"
                image_url = await save_upload_file(image, str(pods_images_dir))

                image_thumbnail_url = None
                try:
                    image_thumbnail_url = (
                        await self._image_service.create_thumbnail_from_image(image)
                    )
                except ValueError:
                    image_thumbnail_url = image_url

                await self._pod_repo.add_pod_image(
                    pod_id=pod_id,
                    image_url=image_url,
                    thumbnail_url=image_thumbnail_url,
                    display_order=index,
                )

                if index == 0:
                    thumbnail_url = image_thumbnail_url

            if thumbnail_url:
                update_fields["thumbnail_url"] = thumbnail_url

        # Pod 기본 정보 업데이트
        if update_fields:
            if "sub_categories" in update_fields and isinstance(
                update_fields["sub_categories"], list
            ):
                update_fields["sub_categories"] = json.dumps(
                    update_fields["sub_categories"], ensure_ascii=False
                )
            await self._pod_repo.update_pod(pod_id, **update_fields)

        # PodDetail 업데이트
        if pod_detail_update_fields:
            await self._pod_repo.update_pod_detail(pod_id, **pod_detail_update_fields)

        # 파티 정보 다시 조회하여 DTO로 변환
        updated_pod = await self._pod_repo.get_pod_by_id(pod_id)
        if updated_pod:
            await self._session.refresh(
                updated_pod, ["detail", "images", "applications", "reviews"]
            )

            # thumbnail_url이 변경되었고 채팅방이 있으면 채팅방 cover_url 업데이트
            if "thumbnail_url" in update_fields and updated_pod.chat_room_id:
                try:
                    chat_room_repo = ChatRoomRepository(self._session)
                    await chat_room_repo.update_cover_url(
                        chat_room_id=updated_pod.chat_room_id,
                        cover_url=updated_pod.thumbnail_url or "",
                    )
                except Exception:
                    pass

            return await self._enrichment_service.enrich(updated_pod, current_user_id)

        return None

    # MARK: - 파티 상태 업데이트
    async def update_pod_status_by_owner(
        self, pod_id: int, status_value: str | None, user_id: int
    ) -> PodDetailDto:
        """파티장이 파티 상태를 변경"""
        if status_value is None:
            raise MissingStatusException()

        try:
            status = PodStatus(status_value.upper())
        except ValueError:
            raise InvalidPodStatusException(status_value)

        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        if pod.owner_id is None or pod.owner_id != user_id:
            raise NoPodAccessPermissionException(pod_id, user_id)

        # 이미 같은 상태인지 확인
        if pod.status == status:
            return await self._enrichment_service.enrich(pod, user_id)

        try:
            # 파티 상태 업데이트
            await self._pod_repo.update_pod_status(pod_id, status)

            # 업데이트된 파티 정보 반환
            updated_pod = await self._pod_repo.get_pod_by_id(pod_id)
            if not updated_pod:
                raise PodNotFoundException(pod_id)

            # 알림 전송
            await self._notification_service.send_pod_status_update_notification(
                pod_id, updated_pod, status
            )

            await self._session.commit()
            return await self._enrichment_service.enrich(updated_pod, user_id)
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 삭제
    async def delete_pod(self, pod_id: int, current_user_id: int) -> None:
        """파티 삭제"""
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        if pod.owner_id != current_user_id:
            raise NoPodAccessPermissionException(pod_id, current_user_id)

        try:
            # 모든 멤버 조회
            all_members = await self._pod_repo.get_pod_members(pod_id)
            member_ids = [member.user_id for member in all_members]

            # 채팅방에서 모든 멤버 제거
            if pod.chat_room_id:
                try:
                    chat_room_repo = ChatRoomRepository(self._session)
                    for member_id in member_ids:
                        await chat_room_repo.remove_member(pod.chat_room_id, member_id)
                    if pod.owner_id is not None:
                        await chat_room_repo.remove_member(
                            pod.chat_room_id, pod.owner_id
                        )
                except Exception:
                    pass

            # 파티장만 데이터베이스에서 제거
            if pod.owner_id is not None:
                await self._pod_repo.remove_pod_member(pod_id, pod.owner_id)

            # 파티 상태를 CANCELED로 변경
            await self._pod_repo.update_pod_status(pod_id, PodStatus.CANCELED)

            # 파티 비활성화 (소프트 삭제)
            if pod:
                setattr(pod, "is_del", True)

            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    # MARK: - 파티 나가기
    async def leave_pod(
        self, pod_id: int, user_id: str | None, current_user_id: int
    ) -> dict:
        """파티 나가기"""
        # user_id 파싱
        if user_id is not None and user_id.strip() != "":
            try:
                target_user_id = int(user_id)
            except ValueError:
                target_user_id = current_user_id
        else:
            target_user_id = current_user_id

        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티장인지 확인
        if pod.owner_id == target_user_id:
            raise PodAccessDeniedException(
                "파티장은 파티 삭제 엔드포인트를 사용해주세요."
            )

        # 멤버인지 확인
        is_member = await self._pod_repo.is_pod_member(pod_id, target_user_id)
        if not is_member:
            raise NoPodAccessPermissionException(pod_id, target_user_id)

        try:
            # 채팅방에서 제거
            if pod.chat_room_id:
                try:
                    chat_room_repo = ChatRoomRepository(self._session)
                    await chat_room_repo.remove_member(pod.chat_room_id, target_user_id)
                except Exception:
                    pass

            # 데이터베이스에서 멤버 제거
            await self._pod_repo.remove_pod_member(pod_id, target_user_id)

            pod_status_value = pod.status.value if pod.status else ""

            await self._session.commit()
            return {
                "left": True,
                "is_owner": False,
                "members_removed": 1,
                "pod_status": pod_status_value,
            }
        except Exception:
            await self._session.rollback()
            raise
