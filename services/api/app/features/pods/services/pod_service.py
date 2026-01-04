import io
import json
import uuid
from datetime import date, datetime, time, timezone
from pathlib import Path

from app.common.schemas import PageDto
from app.core.config import settings
from app.features.chat.repositories.chat_room_repository import ChatRoomRepository
from app.features.follow.services.follow_service import FollowService
from app.features.pods.exceptions import (
    InvalidDateException,
    InvalidImageException,
    PodAccessDeniedException,
    PodNotFoundException,
    PodUpdateFailedException,
)
from app.features.pods.models import (
    Pod,
    PodImage,
    PodStatus,
)
from app.features.pods.repositories.application_repository import (
    ApplicationRepository,
)
from app.features.pods.repositories.like_repository import PodLikeRepository
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import (
    ImageOrderDto,
    PodDetailDto,
    PodForm,
    PodImageDto,
)
from app.features.pods.services.application_service import ApplicationService
from app.features.pods.services.like_service import LikeService
from app.features.pods.services.pod_notification_service import (
    PodNotificationService,
)
from app.features.pods.services.review_service import ReviewService
from app.features.users.exceptions import UserNotFoundException
from app.features.users.repositories import UserRepository
from app.features.users.use_cases.user_use_case import UserUseCase
from app.utils.file_upload import save_upload_file
from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession


class PodService:
    def __init__(
        self,
        session: AsyncSession,
        pod_repo: PodRepository,
        application_repo: ApplicationRepository,
        review_repo: PodReviewRepository,
        like_repo: PodLikeRepository,
        user_repo: UserRepository,
        application_service: ApplicationService,
        user_use_case: UserUseCase,
        notification_service: PodNotificationService,
        review_service: ReviewService,
        like_service: LikeService,
        follow_service: FollowService,
    ):
        self._session = session
        self._pod_repo = pod_repo
        self._application_repo = application_repo
        self._review_repo = review_repo
        self._like_repo = like_repo
        self._user_repo = user_repo
        self._application_service = application_service
        self._user_use_case = user_use_case
        self._review_service = review_service
        self._like_service = like_service
        self._notification_service = notification_service
        self._follow_service = follow_service

    # MARK: - 파티 생성 (Form 데이터에서)
    async def create_pod_from_form(
        self,
        owner_id: int,
        pod_form: PodForm,
        images: list[UploadFile],
        status: PodStatus = PodStatus.RECRUITING,
    ) -> PodDetailDto:
        """Form 데이터로부터 파티 생성 (검증은 use case에서 처리)"""
        # sub_categories를 JSON 문자열에서 리스트로 변환 (필수)
        if not pod_form.sub_categories:
            raise ValueError("sub_categories는 필수입니다.")
        
        try:
            parsed = json.loads(pod_form.sub_categories)
            sub_categories_list = parsed if isinstance(parsed, list) else []
            if not sub_categories_list:
                raise ValueError("sub_categories는 비어있을 수 없습니다.")
        except json.JSONDecodeError:
            raise ValueError("sub_categories는 유효한 JSON 형식이어야 합니다.")
        except Exception as e:
            raise ValueError(f"sub_categories 파싱 실패: {str(e)}")

        # meetingDate(datetime) → date/time 분리
        if not pod_form.meeting_date:
            raise InvalidDateException("meetingDate 필드가 누락되었습니다.")
        
        try:
            # 이미 datetime 객체이므로 UTC로 변환 후 date/time 분리
            dt = pod_form.meeting_date
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)

            parsed_meeting_date: date = dt_utc.date()
            parsed_meeting_time: time = dt_utc.time()
        except (ValueError, AttributeError) as e:
            raise InvalidDateException(str(pod_form.meeting_date)) from e

        result = await self.create_pod(
            owner_id=owner_id,
            title=pod_form.title,
            description=pod_form.description,
            sub_categories=sub_categories_list or [],
            capacity=pod_form.capacity,
            place=pod_form.place,
            address=pod_form.address,
            sub_address=pod_form.sub_address,
            x=pod_form.x,
            y=pod_form.y,
            meeting_date=parsed_meeting_date,
            meeting_time=parsed_meeting_time,
            selected_artist_id=pod_form.selected_artist_id,
            images=images,
            status=status,
        )
        if result is None:
            raise PodUpdateFailedException(0)
        return result

    # MARK: - 파티 생성
    async def create_pod(
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
        images: list[UploadFile | None] = None,
        status: PodStatus = PodStatus.RECRUITING,
    ) -> PodDetailDto | None:
        image_url = None
        thumbnail_url = None

        # 첫 번째 이미지로 thumbnail_url 생성 (임시로 null 저장)
        thumbnail_url = None
        if images:
            first_image = images[0]
            try:
                thumbnail_url = await self._create_thumbnail_from_image(first_image)
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
            image_url=None,  # pods.image_url은 더 이상 사용하지 않음
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
            raise PodNotFoundException(0)  # 생성 실패는 pod_id가 없으므로 0 사용

        # 여러 이미지 저장
        if images:
            pods_images_dir = Path(settings.UPLOADS_DIR) / "pods" / "images"
            for index, image in enumerate(images):
                image_url = await save_upload_file(image, str(pods_images_dir))

                # 각 이미지의 썸네일 생성
                image_thumbnail_url = None
                try:
                    image_thumbnail_url = await self._create_thumbnail_from_image(image)
                except ValueError:
                    image_thumbnail_url = image_url

                # PodImage 저장 (pod_detail_id 사용)
                await self._pod_repo.add_pod_image(
                    pod_detail_id=pod.id,  # pod_detail_id는 pod_id와 동일
                    image_url=image_url,
                    thumbnail_url=image_thumbnail_url,
                    display_order=index,
                )

        # Pod 모델을 PodDetailDto로 변환 (다른 조회 API들과 동일한 방식)
        if pod:
            # PodDetail과 images, applications, reviews 관계를 다시 로드 (MissingGreenlet 오류 방지)
            await self._session.refresh(pod, ["detail", "images", "applications", "reviews"])
            pod_dto = await self._enrich_pod_dto(pod, owner_id)

            # 팔로워들에게 파티 생성 알림 전송
            try:
                pod_id_value = pod.id
                await self._follow_service.send_followed_user_pod_created_notification(
                    owner_id, pod_id_value
                )
            except Exception:
                # 알림 전송 실패는 무시하고 계속 진행
                pass

            return pod_dto
        return None

    async def _create_thumbnail_from_image(self, image: UploadFile) -> str:
        """이미지에서 썸네일을 생성하여 저장"""
        # 이미지 읽기
        image_content = await image.read()

        # 파일 포인터를 다시 처음으로 되돌리기 (다른 곳에서 재사용 가능하도록)
        await image.seek(0)

        # 이미지 파일 검증
        if not image_content:
            raise InvalidImageException("이미지 파일이 비어있습니다")

        try:
            img = Image.open(io.BytesIO(image_content))

            # EXIF 회전 정보 처리
            try:
                ORIENTATION = 274  # EXIF orientation tag number

                # PIL.Image의 getexif() 메서드 사용 (Pillow 6.0+)
                exif = (
                    img.getexif()
                    if hasattr(img, "getexif")
                    else getattr(img, "_getexif", lambda: None)()
                )
                if exif is not None:
                    orientation = exif.get(ORIENTATION)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, TypeError):
                # EXIF 데이터가 없거나 처리할 수 없는 경우 무시
                pass

        except Exception as e:
            raise InvalidImageException(f"이미지 파일을 읽을 수 없습니다: {str(e)}")

        # 썸네일 크기 (300x300)
        thumbnail_size = (300, 300)

        # 썸네일 생성 (비율 유지하며 리사이즈)
        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # 썸네일 저장
        thumbnail_filename = f"{uuid.uuid4()}.jpg"

        # 파일시스템 경로 (실제 저장 위치)
        thumbnails_dir = Path(settings.UPLOADS_DIR) / "pods" / "thumbnails"
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_fs_path = thumbnails_dir / thumbnail_filename

        # RGB로 변환 (JPEG 저장을 위해)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 썸네일 저장
        img.save(str(thumbnail_fs_path), "JPEG", quality=85, optimize=True)

        # URL 경로 반환
        thumbnail_url = f"/uploads/pods/thumbnails/{thumbnail_filename}"
        return thumbnail_url

    # - MARK: 파티 상세 조회
    async def get_pod_detail(
        self, pod_id: int, user_id: int | None = None
    ) -> PodDetailDto:
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        return await self._enrich_pod_dto(pod, user_id)

    # - MARK: 파티 수정
    async def update_pod(self, pod_id: int, **fields) -> Pod | None:
        return await self._pod_repo.update_pod(pod_id, **fields)

    # - MARK: 파티 수정 (이미지 포함)
    # MARK: - 파티 수정 (Form 데이터에서)
    async def update_pod_from_form(
        self,
        pod_id: int,
        current_user_id: int,
        pod_form: PodForm,
        new_images: list[UploadFile | None] = None,
    ) -> PodDetailDto:
        """Form 데이터로부터 파티 수정 (비즈니스 로직 검증 포함)"""
        # 업데이트할 필드들 준비

        # Pod 업데이트 필드
        pod_update_fields = {}
        # PodDetail 업데이트 필드
        pod_detail_update_fields = {}

        # 기본 정보 업데이트
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

        # 날짜와 시간 파싱 (meetingDate: UTC datetime → date/time 분리)
        if pod_form.meeting_date is not None:
            try:
                normalized = pod_form.meeting_date.replace("Z", "+00:00")
                dt = datetime.fromisoformat(normalized)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                dt_utc = dt.astimezone(timezone.utc)

                pod_update_fields["meeting_date"] = dt_utc.date()
                pod_update_fields["meeting_time"] = dt_utc.time()
            except (ValueError, AttributeError) as e:
                raise InvalidDateException(pod_form.meeting_date) from e

        # 파티 업데이트 실행 (이미지 포함)
        updated_pod = await self.update_pod_with_images(
            pod_id=pod_id,
            current_user_id=current_user_id,
            update_fields=pod_update_fields,
            pod_detail_update_fields=pod_detail_update_fields,
            image_orders=pod_form.image_orders,
            new_images=new_images,
        )

        if updated_pod is None:
            raise PodUpdateFailedException(pod_id)

        return updated_pod

    async def update_pod_with_images(
        self,
        pod_id: int,
        current_user_id: int,
        update_fields: dict,
        pod_detail_update_fields: dict | None = None,
        image_orders: str | None = None,
        new_images: list[UploadFile | None] = None,
    ) -> PodDetailDto | None:
        """파티 수정 (이미지 관리 포함)"""
        # 파티 정보 조회 및 권한 확인
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            return None

        # 파티 소유자 확인
        if pod.owner_id != current_user_id:
            raise PodAccessDeniedException(pod_id, current_user_id)

        # 이미지 순서 처리

        if image_orders is not None and image_orders.strip():
            try:
                # JSON 형태로 파싱
                order_data = json.loads(image_orders)
                image_order_objects = [
                    ImageOrderDto.model_validate(item) for item in order_data
                ]

                # 기존 이미지 모두 삭제
                await self._delete_pod_images(pod_id)

                # 새 이미지들을 딕셔너리로 매핑 (인덱스 기반)
                new_images_dict = {}
                if new_images:
                    for i, img in enumerate(new_images):
                        new_images_dict[i] = img

                thumbnail_url = None

                # 순서대로 이미지 처리
                existing_count = 0
                new_count = 0

                for index, order_item in enumerate(image_order_objects):
                    if order_item.type == "existing":
                        # 기존 이미지
                        if order_item.url:
                            await self._pod_repo.add_pod_image(
                                pod_detail_id=pod_id,
                                image_url=order_item.url,
                                thumbnail_url=order_item.url,
                                display_order=index,
                            )
                            existing_count += 1

                            # 첫 번째 이미지면 썸네일로 설정
                            if index == 0:
                                thumbnail_url = order_item.url

                    elif order_item.type == "new":
                        # 새 이미지
                        if (
                            order_item.file_index is not None
                            and order_item.file_index in new_images_dict
                        ):
                            image = new_images_dict[order_item.file_index]

                            # 이미지 저장
                            pods_images_dir = (
                                Path(settings.UPLOADS_DIR) / "pods" / "images"
                            )
                            image_url = await save_upload_file(
                                image, str(pods_images_dir)
                            )

                            # 썸네일 생성
                            image_thumbnail_url = None
                            try:
                                image_thumbnail_url = (
                                    await self._create_thumbnail_from_image(image)
                                )
                            except ValueError:
                                image_thumbnail_url = image_url

                            await self._pod_repo.add_pod_image(
                                pod_detail_id=pod_id,
                                image_url=image_url,
                                thumbnail_url=image_thumbnail_url,
                                display_order=index,
                            )
                            new_count += 1

                            # 첫 번째 이미지면 썸네일로 설정
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

            # 썸네일 업데이트
            if thumbnail_url:
                update_fields["thumbnail_url"] = thumbnail_url

        # 새 이미지만 있는 경우 (image_orders 없이)
        elif new_images:
            # 기존 이미지 모두 삭제
            await self._delete_pod_images(pod_id)

            thumbnail_url = None

            # 새 이미지들을 순서대로 추가
            for index, image in enumerate(new_images):
                # 이미지 저장
                pods_images_dir = Path(settings.UPLOADS_DIR) / "pods" / "images"
                image_url = await save_upload_file(image, str(pods_images_dir))

                # 썸네일 생성
                image_thumbnail_url = None
                try:
                    image_thumbnail_url = await self._create_thumbnail_from_image(image)
                except ValueError:
                    image_thumbnail_url = image_url

                await self._pod_repo.add_pod_image(
                    pod_detail_id=pod_id,
                    image_url=image_url,
                    thumbnail_url=image_thumbnail_url,
                    display_order=index,
                )

                # 첫 번째 이미지면 썸네일로 설정
                if index == 0:
                    thumbnail_url = image_thumbnail_url

            # 썸네일 업데이트
            if thumbnail_url:
                update_fields["thumbnail_url"] = thumbnail_url

        # Pod 기본 정보 업데이트
        if update_fields:
            # sub_categories를 JSON 문자열로 변환
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
            await self._session.refresh(updated_pod, ["detail", "images", "applications", "reviews"])

            # thumbnail_url이 변경되었고 채팅방이 있으면 채팅방 cover_url 업데이트
            if "thumbnail_url" in update_fields and updated_pod.chat_room_id:
                try:
                    chat_room_repo = ChatRoomRepository(self._session)
                    await chat_room_repo.update_cover_url(
                        chat_room_id=updated_pod.chat_room_id,
                        cover_url=updated_pod.thumbnail_url or "",
                    )
                except Exception:
                    # 채팅방 업데이트 실패는 파티 업데이트를 막지 않음
                    pass

            pod_dto = await self._enrich_pod_dto(updated_pod, current_user_id)
            return pod_dto

        return None

    async def _delete_pod_images(self, pod_id: int):
        """파티의 모든 이미지 삭제 (PodDetail의 images 삭제)"""
        await self._pod_repo.delete_pod_images(pod_id)

    # - MARK: 파티 상태 업데이트 (파티장만 가능)
    async def update_pod_status_by_owner(
        self, pod_id: int, status: PodStatus, user_id: int
    ) -> PodDetailDto:
        """파티장이 파티 상태를 변경 (검증은 use case에서 처리)"""
        # 파티 조회
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 이미 같은 상태인지 확인
        if pod.status == status:
            return await self._enrich_pod_dto(pod, user_id)

        # 파티 상태 업데이트
        await self._pod_repo.update_pod_status(pod_id, status)

        # 업데이트된 파티 정보 반환
        updated_pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not updated_pod:
            raise PodNotFoundException(pod_id)
        return await self._enrich_pod_dto(updated_pod, user_id)

    # - MARK: 파티 완료 처리 (하위 호환성을 위해 유지)
    async def complete_pod(self, pod_id: int, user_id: int) -> PodDetailDto:
        """파티장이 파티를 완료 상태로 변경 (하위 호환성)"""
        return await self.update_pod_status_by_owner(pod_id, "COMPLETED", user_id)

    # - MARK: 파티 나가기
    async def leave_pod(
        self, pod_id: int, user_id: str | None, current_user_id: int
    ) -> dict:
        """파티 나가기 (파티장이면 모든 멤버 강제 퇴장, 일반 멤버면 본인만)"""
        # user_id가 제공되면 사용, 없으면 토큰에서 추출한 사용자 ID 사용
        if user_id is not None and user_id.strip() != "":
            try:
                target_user_id = int(user_id)
            except ValueError:
                # 잘못된 정수 형식인 경우 현재 사용자 사용
                target_user_id = current_user_id
        else:
            target_user_id = current_user_id

        # 파티 조회
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 파티장인지 확인
        is_owner = pod.owner_id is not None and pod.owner_id == target_user_id

        if is_owner:
            # 파티장이 나가는 경우 - 멤버는 유지하고 채팅방에서만 모두 제거

            # 모든 멤버 조회
            all_members = await self._pod_repo.get_pod_members(pod_id)
            member_ids = [member.user_id for member in all_members]

            # 채팅방에서 모든 멤버 제거
            if pod.chat_room_id:
                try:
                    chat_room_repo = ChatRoomRepository(self._session)
                    # 모든 멤버를 채팅방에서 제거
                    for member_id in member_ids:
                        await chat_room_repo.remove_member(pod.chat_room_id, member_id)

                    # 파티장도 채팅방에서 제거
                    await chat_room_repo.remove_member(pod.chat_room_id, target_user_id)

                except Exception:
                    # 채팅방 멤버 제거 실패는 무시
                    pass

            # 파티장만 데이터베이스에서 제거 (멤버는 유지하여 상태 확인 가능하도록)
            # 멤버는 그대로 두고 파티장만 나가기
            await self._pod_repo.remove_pod_member(pod_id, target_user_id)

            # 파티 상태를 CANCELED로 변경
            await self._pod_repo.update_pod_status(pod_id, PodStatus.CANCELED)

            # 파티 비활성화 (소프트 삭제)
            await self._pod_repo.update_pod(pod_id, is_del=True)

            return {
                "left": True,
                "is_owner": True,
                "members_removed": 0,  # 멤버는 유지하므로 0
                "pod_status": PodStatus.CANCELED.value,
            }

        else:
            # 일반 멤버가 나가는 경우 - 본인만 나가기 (권한 확인은 use case에서 처리)

            # 채팅방에서 제거
            if pod.chat_room_id:
                try:
                    chat_room_repo = ChatRoomRepository(self._session)
                    await chat_room_repo.remove_member(pod.chat_room_id, target_user_id)

                except Exception:
                    # 채팅방 제거 실패는 무시
                    pass

            # 데이터베이스에서 멤버 제거
            await self._pod_repo.remove_pod_member(pod_id, target_user_id)

            pod_status_value = pod.status.value if pod.status else ""

            return {
                "left": True,
                "is_owner": False,
                "members_removed": 1,
                "pod_status": pod_status_value,
            }

    # - MARK: 파티 삭제
    async def delete_pod(self, pod_id: int) -> None:
        """파티 삭제 (파티장이 나가는 것과 동일한 로직)"""
        # 파티 조회
        pod = await self._pod_repo.get_pod_by_id(pod_id)
        if not pod:
            raise PodNotFoundException(pod_id)

        # 모든 멤버 조회
        all_members = await self._pod_repo.get_pod_members(pod_id)
        member_ids = [member.user_id for member in all_members]

        # 채팅방에서 모든 멤버 제거
        if pod.chat_room_id:
            try:
                chat_room_repo = ChatRoomRepository(self._session)
                # 모든 멤버를 채팅방에서 제거
                for member_id in member_ids:
                    await chat_room_repo.remove_member(pod.chat_room_id, member_id)

                # 파티장도 채팅방에서 제거
                if pod.owner_id is not None:
                    await chat_room_repo.remove_member(pod.chat_room_id, pod.owner_id)

            except Exception:
                # 채팅방 멤버 제거 실패는 무시
                pass

        # 파티장만 데이터베이스에서 제거 (멤버는 유지하여 상태 확인 가능하도록)
        if pod.owner_id is not None:
            await self._pod_repo.remove_pod_member(pod_id, pod.owner_id)

        # 파티 상태를 CANCELED로 변경
        await self._pod_repo.update_pod_status(pod_id, PodStatus.CANCELED)

        # 파티 비활성화 (소프트 삭제)
        if pod:
            setattr(pod, "is_del", True)

    # - MARK: 요즘 인기 있는 파티 조회
    async def get_trending_pods(
        self, user_id: int, selected_artist_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """
        요즘 인기 있는 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 7일 이내 인기도 기반 정렬
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_trending_pods(
            user_id, selected_artist_id, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        # TODO: 실제 total_count를 가져오는 로직 추가 필요
        total_count = len(pod_dtos)  # 임시로 현재 페이지 아이템 수 사용

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 마감 직전 파티 조회
    async def get_closing_soon_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDetailDto]:
        """
        마감 직전 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 에디터가 설정한 지역 (선택사항)
        - 24시간 이내 마감 모임 우선 정렬
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_closing_soon_pods(
            user_id, selected_artist_id, location, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 우리 만난적 있어요 파티 조회
    async def get_history_based_pods(
        self, user_id: int, selected_artist_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """
        우리 만난적 있어요 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 이전 매칭 사용자 기반 추천
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_history_based_pods(
            user_id, selected_artist_id, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 인기 최고 카테고리 파티 조회
    async def get_popular_categories_pods(
        self,
        user_id: int,
        selected_artist_id: int,
        location: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDetailDto]:
        """
        인기 최고 카테고리 파티 조회
        - 현재 선택된 아티스트 기준
        - 마감되지 않은 파티
        - 최근 일주일 기준 인기 카테고리 기반 추천
        - 페이지네이션 지원
        """
        pods = await self._pod_repo.get_popular_categories_pods(
            user_id, selected_artist_id, location, page, size
        )

        # SQLAlchemy 모델을 DTO로 변환 (참여자 수, 좋아요 수 포함)
        pod_dtos = []
        for pod in pods:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    # - MARK: 특정 유저가 개설한 파티 목록 조회
    async def get_user_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """특정 유저가 개설한 파티 목록 조회 (비즈니스 로직 검증 포함)"""
        # 사용자 존재 확인
        user = await self._user_repo.get_by_id(user_id)
        if not user or user.is_del:
            raise UserNotFoundException(user_id)
        try:
            result = await self._pod_repo.get_user_pods(user_id, page, size)
            pods = result["items"]
            total_count = result["total_count"]

            pod_dtos = []
            for pod in pods:
                try:
                    pod_dto = await self._enrich_pod_dto(pod, user_id)
                    pod_dtos.append(pod_dto)
                except Exception:
                    # 에러 발생 시 해당 파티는 건너뛰고 계속 진행
                    continue

        except Exception:
            raise

        return PageDto.create(
            items=pod_dtos,
            page=page,
            size=size,
            total_count=total_count,
        )

    async def search_pods(
        self,
        user_id: int | None = None,
        title: str | None = None,
        main_category: str | None = None,
        sub_category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        location: list[str | None] = None,
        page: int = 1,
        size: int = 20,
    ) -> PageDto[PodDetailDto]:
        """팟 검색 (검증은 use case에서 처리)"""
        result = await self._pod_repo.search_pods(
            query=title or "",
            main_category=main_category,
            sub_categories=[sub_category] if sub_category else None,
            start_date=start_date,
            end_date=end_date,
            location=location[0] if location and len(location) > 0 else None,
            page=page,
            size=size,
        )

        # DTO 변환
        pod_dtos = []
        for pod in result["items"]:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        # PageDto 생성
        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # - MARK: 사용자가 참여한 파티 조회
    async def get_user_joined_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """사용자가 참여한 파티 목록 조회"""
        result = await self._pod_repo.get_user_joined_pods(user_id, page, size)

        # DTO 변환
        pod_dtos = []
        for pod in result["items"]:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # - MARK: 사용자가 좋아요한 파티 조회
    async def get_user_liked_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDetailDto]:
        """사용자가 좋아요한 파티 목록 조회"""
        result = await self._pod_repo.get_user_liked_pods(user_id, page, size)

        # DTO 변환
        pod_dtos = []
        for pod in result["items"]:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dto.is_liked = True  # 좋아요한 파티이므로 항상 True
            pod_dtos.append(pod_dto)

        return PageDto.create(
            items=pod_dtos,
            page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
        )

    # MARK: - 헬퍼 메서드
    def _parse_sub_categories_from_storage(
        self, sub_categories_raw: str | list[str] | None
    ) -> list[str]:
        """저장된 sub_categories를 리스트로 변환 (데이터 변환 로직)"""
        if sub_categories_raw is None:
            return []
        if isinstance(sub_categories_raw, list):
            return sub_categories_raw
        if isinstance(sub_categories_raw, str):
            try:
                parsed = json.loads(sub_categories_raw)
                return parsed if isinstance(parsed, list) else []
            except (ValueError, TypeError, json.JSONDecodeError):
                return []
        return []

    # MARK: - 헬퍼 메서드

    async def _enrich_pod_dto(
        self, pod: Pod, user_id: int | None = None
    ) -> PodDetailDto:
        """Pod를 PodDetailDto로 변환하고 추가 정보를 설정"""

        # PodDetail 조회
        pod_detail = pod.detail

        # 이미지 리스트 조회
        images_dto = []
        if pod.images:
            # display_order로 정렬
            pod_images: list[PodImage] = list(pod.images)
            for img in sorted(pod_images, key=lambda x: x.display_order or 0):
                images_dto.append(PodImageDto.from_pod_image(img))

        # Pod 속성 추출
        pod_sub_categories_raw = pod.sub_categories

        # datetime 기본값 제공
        pod_created_at = pod.created_at
        if pod_created_at is None:
            pod_created_at = datetime.now(timezone.utc).replace(tzinfo=None)

        pod_updated_at = pod.updated_at
        if pod_updated_at is None:
            pod_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # sub_categories 파싱 (이미 저장된 데이터 변환)
        pod_sub_categories = self._parse_sub_categories_from_storage(
            pod_sub_categories_raw
        )

        # status 변환
        from app.features.pods.models import PodStatus

        # PodDetailDto를 수동으로 생성하여 applications 필드 접근 방지
        pod_status = pod.status
        if pod_status is None:
            pod_status = PodStatus.RECRUITING
        elif isinstance(pod_status, str):
            try:
                pod_status = PodStatus(pod_status.upper())
            except ValueError:
                pod_status = PodStatus.RECRUITING

        pod_dto = PodDetailDto(
            id=pod.id or 0,
            owner_id=pod.owner_id or 0,
            title=pod.title or "",
            description=pod_detail.description if pod_detail else "",
            image_url=pod_detail.image_url if pod_detail else None,
            thumbnail_url=pod.thumbnail_url,
            sub_categories=pod_sub_categories,
            capacity=pod.capacity or 0,
            place=pod.place or "",
            address=pod_detail.address if pod_detail else "",
            sub_address=pod_detail.sub_address if pod_detail else None,
            x=pod_detail.x if pod_detail else None,
            y=pod_detail.y if pod_detail else None,
            meeting_date=pod.meeting_date if pod.meeting_date else date.today(),
            meeting_time=pod.meeting_time if pod.meeting_time else time.min,
            selected_artist_id=pod.selected_artist_id,
            status=pod_status,
            is_del=pod.is_del if pod.is_del else False,
            chat_room_id=pod.chat_room_id,
            images=images_dto,
            created_at=pod_created_at,
            updated_at=pod_updated_at,
            # 기본값 설정
            is_liked=False,
            my_application=None,
            applications=[],
            view_count=0,
            joined_users_count=0,
            like_count=0,
            joined_users=[],
        )

        # 통계 필드 설정
        if pod.id is not None:
            pod_dto.joined_users_count = await self._pod_repo.get_joined_users_count(
                pod.id
            )
            pod_dto.like_count = await self._like_repo.like_count(pod.id)
            pod_dto.view_count = await self._pod_repo.get_view_count(pod.id)

        # 참여 중인 유저 목록 조회 (파티장 + 멤버들)
        if pod.id is None:
            return pod_dto
        pod_members = await self._application_repo.list_members(pod.id)

        # 차단된 유저 필터링 제거 (joined_users에서 모든 유저 표시)

        # PodMember를 UserDto로 변환
        joined_users = []

        # 1. 파티장 추가
        # 파티장 정보 조회
        if pod.owner_id is not None:
            owner = await self._user_repo.get_by_id(pod.owner_id)

            if owner:
                # 파티장 성향 타입 조회
                owner_tendency_type = await self._user_repo.get_user_tendency_type(
                    pod.owner_id
                )

                # UserDto 생성
                from app.features.users.services.user_dto_service import (
                    UserDtoService,
                )

                owner_dto = UserDtoService.create_user_dto(
                    owner, owner_tendency_type or ""
                )
                joined_users.append(owner_dto)

        # 2. 멤버들 추가
        for member in pod_members:
            if member.user_id is None:
                continue

            # User 정보 조회
            user = await self._user_repo.get_by_id(member.user_id)

            if user:
                # 성향 타입 조회
                tendency_type = await self._user_repo.get_user_tendency_type(
                    member.user_id
                )

                # UserDto 생성
                from app.features.users.services.user_dto_service import (
                    UserDtoService,
                )

                user_dto = UserDtoService.create_user_dto(user, tendency_type or "")
                joined_users.append(user_dto)

        pod_dto.joined_users = joined_users

        # 사용자 정보가 있으면 개인화 필드 설정
        if user_id and pod.id is not None:
            pod_dto.is_liked = await self._pod_repo.is_liked_by_user(pod.id, user_id)

            # 사용자의 신청서 정보 조회
            user_applications = (
                await self._application_repo.get_applications_by_user_id(user_id)
            )
            user_application = (
                next(
                    (app for app in user_applications if app.pod_id == pod.id),
                    None,
                )
                if pod.id is not None
                else None
            )

            if user_application:
                # 신청한 사용자 정보 조회
                if user_application.user_id is not None:
                    app_user = await self._user_repo.get_by_id(user_application.user_id)

                    if app_user:
                        # 성향 타입 조회
                        tendency_type = await self._user_repo.get_user_tendency_type(
                            user_application.user_id
                        )

                        # UserDto 생성
                        from app.features.users.services.user_dto_service import (
                            UserDtoService,
                        )

                        user_dto = UserDtoService.create_user_dto(
                            app_user, tendency_type or ""
                        )

                        # PodApplDto 생성
                        pod_dto.my_application = (
                            self._application_service._create_pod_appl_dto(
                                user_application, user_dto, include_message=True
                            )
                        )

        # 파티에 들어온 신청서 목록 조회
        if pod.id is None:
            return pod_dto
        # Pod에서 applications 가져오기
        if pod.applications:
            applications = list(pod.applications)
        else:
            applications = await self._application_repo.get_applications_by_pod_id(
                pod.id
            )

        application_dtos = []
        for app in applications:
            # 신청한 사용자 정보 조회
            if app.user_id is None:
                continue

            app_user = await self._user_repo.get_by_id(app.user_id)

            if app_user:
                # 성향 타입 조회
                tendency_type = await self._user_repo.get_user_tendency_type(
                    app.user_id
                )

                # UserDto 생성
                from app.features.users.services.user_dto_service import (
                    UserDtoService,
                )

                user_dto = UserDtoService.create_user_dto(
                    app_user, tendency_type or ""
                )

                # PodApplDto 생성
                application_dto = self._application_service._create_pod_appl_dto(
                    app, user_dto, include_message=True
                )
                application_dtos.append(application_dto)

        pod_dto.applications = application_dtos

        # 후기 목록 조회 및 추가
        if pod.id is None:
            return pod_dto
        # Pod에서 reviews 가져오기
        if pod.reviews:
            reviews = list(pod.reviews)
        else:
            reviews = await self._review_repo.get_all_reviews_by_pod(pod.id)

        review_dtos = []
        for review in reviews:
            review_dto = await self._review_service._convert_to_dto(review)
            review_dtos.append(review_dto)

        pod_dto.reviews = review_dtos
        return pod_dto
