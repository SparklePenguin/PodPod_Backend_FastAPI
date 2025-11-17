from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, time
from app.crud.pod.pod import PodCRUD
from app.crud.pod.pod_application import PodApplicationCRUD
from app.schemas.pod import PodCreateRequest, PodDto
from app.schemas.pod.simple_application_dto import SimpleApplicationDto
from app.schemas.pod.image_order import ImageOrder
from app.schemas.common import PageDto
from app.utils.file_upload import save_upload_file
from fastapi import UploadFile
from app.models.pod import Pod
from app.models.pod.pod_status import PodStatus
from app.services.fcm_service import FCMService
from app.crud.user import UserCRUD
from app.models.user import User
from app.core.error_codes import raise_error
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import date
import math
import logging

logger = logging.getLogger(__name__)


class PodService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodCRUD(db)
        self.application_crud = PodApplicationCRUD(db)
        from app.crud.pod_review import PodReviewCRUD

        self.review_crud = PodReviewCRUD(db)

    # - MARK: 파티 생성
    async def create_pod(
        self,
        owner_id: int,
        req: PodCreateRequest,
        images: list[UploadFile] = None,
        status: PodStatus = PodStatus.RECRUITING,
    ) -> Optional[PodDto]:
        from app.models.pod.pod_image import PodImage

        image_url = None
        thumbnail_url = None

        # 첫 번째 이미지로 thumbnail_url 생성 (임시로 null 저장)
        thumbnail_url = None
        if images:
            first_image = images[0]
            try:
                thumbnail_url = await self._create_thumbnail_from_image(first_image)
            except ValueError as e:
                thumbnail_url = await save_upload_file(
                    first_image, "uploads/pods/images"
                )

        # 파티 생성 (채팅방 포함)
        pod = await self.crud.create_pod_with_chat(
            owner_id=owner_id,
            title=req.title,
            description=req.description,
            image_url=None,  # pods.image_url은 더 이상 사용하지 않음
            thumbnail_url=thumbnail_url,
            sub_categories=req.sub_categories,
            capacity=req.capacity,
            place=req.place,
            address=req.address,
            sub_address=req.sub_address,
            meeting_date=req.meetingDate,
            meeting_time=req.meetingTime,
            selected_artist_id=req.selected_artist_id,
            x=req.x,
            y=req.y,
            status=status,
        )

        # 여러 이미지 저장
        if pod and images:
            for index, image in enumerate(images):
                image_url = await save_upload_file(image, "uploads/pods/images")

                # 각 이미지의 썸네일 생성
                image_thumbnail_url = None
                try:
                    image_thumbnail_url = await self._create_thumbnail_from_image(image)
                except ValueError as e:
                    image_thumbnail_url = image_url

                # PodImage 저장
                pod_image = PodImage(
                    pod_id=pod.id,
                    image_url=image_url,
                    thumbnail_url=image_thumbnail_url,
                    display_order=index,
                )
                self.db.add(pod_image)

            await self.db.commit()

        # Pod 모델을 PodDto로 변환 (다른 조회 API들과 동일한 방식)
        if pod:
            # images 관계를 다시 로드 (MissingGreenlet 오류 방지)
            await self.db.refresh(pod, ["images"])
            pod_dto = await self._enrich_pod_dto(pod, owner_id)

            # 팔로워들에게 파티 생성 알림 전송
            try:
                from app.services.follow_service import FollowService

                follow_service = FollowService(self.db)
                await follow_service.send_followed_user_pod_created_notification(
                    owner_id, pod.id
                )
            except Exception as e:
                logger.error(
                    f"팔로워 파티 생성 알림 전송 실패: owner_id={owner_id}, pod_id={pod.id}, error={e}"
                )

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

        # 파일 포인터를 다시 처음으로 되돌리기 (다른 곳에서 재사용 가능하도록)
        await image.seek(0)

        # 이미지 파일 검증
        if not image_content:
            raise ValueError("이미지 파일이 비어있습니다")

        try:
            img = Image.open(io.BytesIO(image_content))

            # EXIF 회전 정보 처리
            try:
                from PIL.ExifTags import ORIENTATION

                exif = img._getexif()
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
            raise ValueError(f"이미지 파일을 읽을 수 없습니다: {str(e)}")

        # 썸네일 크기 (300x300)
        thumbnail_size = (300, 300)

        # 썸네일 생성 (비율 유지하며 리사이즈)
        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # 썸네일 저장
        thumbnail_filename = f"{uuid.uuid4()}.jpg"
        thumbnail_path = f"/uploads/pods/thumbnails/{thumbnail_filename}"

        # 디렉토리 생성
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

        # RGB로 변환 (JPEG 저장을 위해)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 썸네일 저장
        img.save(thumbnail_path, "JPEG", quality=85, optimize=True)

        return thumbnail_path

    # - MARK: 파티 상세 조회
    async def get_pod_detail(
        self, pod_id: int, user_id: Optional[int] = None
    ) -> Optional[PodDto]:
        pod = await self.crud.get_pod_by_id(pod_id)
        if not pod:
            return None

        return await self._enrich_pod_dto(pod, user_id)

    # - MARK: 파티 수정
    async def update_pod(self, pod_id: int, **fields) -> Optional[Pod]:
        return await self.crud.update_pod(pod_id, **fields)

    # - MARK: 파티 수정 (이미지 포함)
    async def update_pod_with_images(
        self,
        pod_id: int,
        current_user_id: int,
        update_fields: dict,
        image_orders: Optional[str] = None,
        new_images: Optional[list[UploadFile]] = None,
    ) -> Optional[PodDto]:
        """파티 수정 (이미지 관리 포함)"""
        from app.models.pod.pod_image import PodImage
        import json

        # 파티 정보 조회 및 권한 확인
        pod = await self.crud.get_pod_by_id(pod_id)
        if not pod:
            return None

        # 파티 소유자 확인
        if pod.owner_id != current_user_id:
            raise_error("POD_ACCESS_DENIED")

        # 이미지 순서 처리
        logger.info(f"[파티 업데이트] image_orders 값: '{image_orders}'")
        logger.info(f"[파티 업데이트] image_orders 타입: {type(image_orders)}")
        logger.info(
            f"[파티 업데이트] new_images 개수: {len(new_images) if new_images else 0}"
        )

        if image_orders is not None and image_orders.strip():
            try:
                # JSON 형태로 파싱
                logger.info(f"[파티 업데이트] JSON 파싱 시도: {image_orders}")
                order_data = json.loads(image_orders)
                image_order_objects = [
                    ImageOrder.model_validate(item) for item in order_data
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
                    logger.info(
                        f"[파티 업데이트] 처리 중인 이미지 {index}: type={order_item.type}, url={order_item.url}, fileIndex={order_item.file_index}"
                    )

                    if order_item.type == "existing":
                        # 기존 이미지
                        if order_item.url:
                            pod_image = PodImage(
                                pod_id=pod_id,
                                image_url=order_item.url,
                                thumbnail_url=order_item.url,
                                display_order=index,
                            )
                            self.db.add(pod_image)
                            existing_count += 1

                            # 첫 번째 이미지면 썸네일로 설정
                            if index == 0:
                                thumbnail_url = order_item.url

                            logger.info(
                                f"[파티 업데이트] 기존 이미지 추가: {order_item.url}"
                            )

                    elif order_item.type == "new":
                        # 새 이미지
                        if (
                            order_item.file_index is not None
                            and order_item.file_index in new_images_dict
                        ):
                            image = new_images_dict[order_item.file_index]

                            # 이미지 저장
                            image_url = await save_upload_file(
                                image, "uploads/pods/images"
                            )

                            # 썸네일 생성
                            image_thumbnail_url = None
                            try:
                                image_thumbnail_url = (
                                    await self._create_thumbnail_from_image(image)
                                )
                            except ValueError as e:
                                image_thumbnail_url = image_url

                            pod_image = PodImage(
                                pod_id=pod_id,
                                image_url=image_url,
                                thumbnail_url=image_thumbnail_url,
                                display_order=index,
                            )
                            self.db.add(pod_image)
                            new_count += 1

                            # 첫 번째 이미지면 썸네일로 설정
                            if index == 0:
                                thumbnail_url = image_thumbnail_url

                            logger.info(f"[파티 업데이트] 새 이미지 추가: {image_url}")
                        else:
                            logger.warning(
                                f"[파티 업데이트] 새 이미지 파일을 찾을 수 없음: fileIndex={order_item.file_index}, 사용 가능한 파일: {list(new_images_dict.keys())}"
                            )

                # 썸네일 업데이트
                if thumbnail_url:
                    update_fields["thumbnail_url"] = thumbnail_url

                logger.info(
                    f"[파티 업데이트] 이미지 처리 완료: 총 {len(image_order_objects)}개 (기존: {existing_count}개, 새: {new_count}개)"
                )

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"이미지 순서 파싱 오류: {e}")
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "BAD_REQUEST",
                        "code": 4000,
                        "message": "이미지 순서 데이터가 올바르지 않습니다.",
                    },
                )

        # 새 이미지만 있는 경우 (image_orders 없이)
        elif new_images:
            logger.info(f"[파티 업데이트] 새 이미지만 처리: {len(new_images)}개")

            # 기존 이미지 모두 삭제
            await self._delete_pod_images(pod_id)

            thumbnail_url = None

            # 새 이미지들을 순서대로 추가
            for index, image in enumerate(new_images):
                logger.info(
                    f"[파티 업데이트] 새 이미지 처리 중 {index}: {image.filename}"
                )

                # 이미지 저장
                image_url = await save_upload_file(image, "uploads/pods/images")

                # 썸네일 생성
                image_thumbnail_url = None
                try:
                    image_thumbnail_url = await self._create_thumbnail_from_image(image)
                except ValueError as e:
                    image_thumbnail_url = image_url

                pod_image = PodImage(
                    pod_id=pod_id,
                    image_url=image_url,
                    thumbnail_url=image_thumbnail_url,
                    display_order=index,
                )
                self.db.add(pod_image)

                # 첫 번째 이미지면 썸네일로 설정
                if index == 0:
                    thumbnail_url = image_thumbnail_url

                logger.info(f"[파티 업데이트] 새 이미지 저장 완료: {image_url}")

            # 썸네일 업데이트
            if thumbnail_url:
                update_fields["thumbnail_url"] = thumbnail_url

            logger.info(f"[파티 업데이트] 새 이미지만 처리 완료: {len(new_images)}개")

        # 파티 기본 정보 업데이트
        if update_fields:
            # sub_categories를 JSON 문자열로 변환
            if "sub_categories" in update_fields and isinstance(
                update_fields["sub_categories"], list
            ):
                import json

                update_fields["sub_categories"] = json.dumps(
                    update_fields["sub_categories"], ensure_ascii=False
                )

            await self.crud.update_pod(pod_id, **update_fields)

        await self.db.commit()

        # 파티 정보 다시 조회하여 DTO로 변환
        updated_pod = await self.crud.get_pod_by_id(pod_id)
        if updated_pod:
            await self.db.refresh(updated_pod, ["images"])

            # thumbnail_url이 변경되었고 채팅방이 있으면 Sendbird 채널 cover_url 업데이트
            if "thumbnail_url" in update_fields and updated_pod.chat_channel_url:
                try:
                    from app.services.sendbird_service import SendbirdService

                    sendbird_service = SendbirdService()
                    await sendbird_service.update_channel_cover_url(
                        channel_url=updated_pod.chat_channel_url,
                        cover_url=updated_pod.thumbnail_url or "",
                    )
                    logger.info(
                        f"Sendbird 채널 cover_url 업데이트 완료: pod_id={pod_id}, channel_url={updated_pod.chat_channel_url}"
                    )
                except Exception as e:
                    logger.error(
                        f"Sendbird 채널 cover_url 업데이트 실패: pod_id={pod_id}, error={e}"
                    )
                    # 채널 업데이트 실패는 파티 업데이트를 막지 않음

            pod_dto = await self._enrich_pod_dto(updated_pod, current_user_id)

            # 알림 전송
            await self._send_pod_update_notification(pod_id, updated_pod)

            return pod_dto

        return None

    async def _delete_pod_images(self, pod_id: int):
        """파티의 모든 이미지 삭제"""
        from app.models.pod.pod_image import PodImage

        result = await self.db.execute(
            select(PodImage).where(PodImage.pod_id == pod_id)
        )
        images = result.scalars().all()

        for image in images:
            await self.db.delete(image)

    async def _send_pod_update_notification(self, pod_id: int, pod: Pod):
        """파티 수정 알림 전송"""
        try:
            fcm_service = FCMService()
            participants = await self.crud.get_pod_participants(pod_id)

            for participant in participants:
                if participant.id != pod.owner_id and participant.fcm_token:
                    try:
                        await fcm_service.send_pod_updated(
                            token=participant.fcm_token,
                            party_name=pod.title,
                            pod_id=pod_id,
                            db=self.db,
                            user_id=participant.id,
                            related_user_id=pod.owner_id,
                        )
                        logger.info(
                            f"파티 수정 알림 전송 성공: user_id={participant.id}, pod_id={pod_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"파티 수정 알림 전송 실패: user_id={participant.id}, error={e}"
                        )
        except Exception as e:
            logger.error(f"파티 수정 알림 처리 중 오류: {e}")

    # - MARK: 파티 수정 (알림 포함)
    async def update_pod_with_notification(
        self, pod_id: int, **fields
    ) -> Optional[Pod]:
        """파티 수정 후 모든 참여자에게 알림 전송"""
        # 파티 정보 조회
        pod = await self.crud.get_pod_by_id(pod_id)
        if not pod:
            return None

        # 파티 수정 실행
        updated_pod = await self.crud.update_pod(pod_id, **fields)
        if not updated_pod:
            return None

        try:
            # FCM 서비스 초기화
            fcm_service = FCMService()
            user_crud = UserCRUD(self.db)

            # 파티 참여자 목록 조회 (파티장 포함)
            participants = await self.crud.get_pod_participants(pod_id)

            # 파티장 제외하고 알림 전송
            for participant in participants:
                if participant.id != pod.owner_id:
                    try:
                        # 사용자 FCM 토큰 확인
                        if participant.fcm_token:
                            await fcm_service.send_pod_updated(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod_id,
                                db=self.db,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                            logger.info(
                                f"파티 수정 알림 전송 성공: user_id={participant.id}, pod_id={pod_id}"
                            )
                        else:
                            logger.warning(
                                f"FCM 토큰이 없는 사용자: user_id={participant.id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"파티 수정 알림 전송 실패: user_id={participant.id}, error={e}"
                        )

        except Exception as e:
            logger.error(f"파티 수정 알림 처리 중 오류: {e}")

        return updated_pod

    # - MARK: 파티 상태 업데이트 (파티장만 가능)
    async def update_pod_status_by_owner(
        self, pod_id: int, status: PodStatus, user_id: int
    ) -> bool:
        """파티장이 파티 상태를 변경"""
        logger.info(
            f"파티 상태 업데이트 시도: pod_id={pod_id}, status={status.value}, user_id={user_id}"
        )

        # 파티 조회
        pod = await self.crud.get_pod_by_id(pod_id)
        if not pod:
            logger.error(f"파티를 찾을 수 없음: pod_id={pod_id}")
            raise_error("POD_NOT_FOUND")

        # 파티장 권한 확인
        if pod.owner_id != user_id:
            logger.error(
                f"파티장 권한 없음: pod_owner_id={pod.owner_id}, 요청 user_id={user_id}"
            )
            raise_error("NO_POD_ACCESS_PERMISSION")

        # 이미 같은 상태인지 확인
        if pod.status == status:
            logger.warning(f"이미 {status.value} 상태인 파티: pod_id={pod_id}")
            return True

        logger.info(
            f"파티 상태 업데이트 진행: pod_id={pod_id}, {pod.status.value} -> {status.value}"
        )
        # 파티 상태를 변경하고 알림 전송
        return await self.update_pod_status_with_notification(pod_id, status)

    # - MARK: 파티 완료 처리 (하위 호환성을 위해 유지)
    async def complete_pod(self, pod_id: int, user_id: int) -> bool:
        """파티장이 파티를 완료 상태로 변경 (하위 호환성)"""
        return await self.update_pod_status_by_owner(
            pod_id, PodStatus.COMPLETED, user_id
        )

    # - MARK: 파티 나가기
    async def leave_pod(self, pod_id: int, user_id: int) -> dict:
        """파티 나가기 (파티장이면 모든 멤버 강제 퇴장, 일반 멤버면 본인만)"""
        logger.info(f"파티 나가기 시도: pod_id={pod_id}, user_id={user_id}")

        # 파티 조회
        pod = await self.crud.get_pod_by_id(pod_id)
        if not pod:
            logger.error(f"파티를 찾을 수 없음: pod_id={pod_id}")
            raise_error("POD_NOT_FOUND")

        # 파티장인지 확인
        is_owner = pod.owner_id == user_id

        if is_owner:
            # 파티장이 나가는 경우 - 모든 멤버 강제 퇴장
            logger.info(f"파티장이 나가는 경우: pod_id={pod_id}, owner_id={user_id}")

            # 모든 멤버 조회
            all_members = await self.crud.get_pod_members(pod_id)
            member_ids = [member.user_id for member in all_members]

            # Sendbird 채팅방에서 모든 멤버 제거
            if pod.chat_channel_url:
                try:
                    from app.services.sendbird_service import SendbirdService

                    sendbird_service = SendbirdService()

                    # 모든 멤버를 채팅방에서 제거
                    for member_id in member_ids:
                        success = await sendbird_service.remove_member_from_channel(
                            channel_url=pod.chat_channel_url, user_id=str(member_id)
                        )
                        if success:
                            logger.info(f"멤버 {member_id}를 채팅방에서 제거 완료")
                        else:
                            logger.warning(f"멤버 {member_id} 채팅방 제거 실패")

                    # 파티장도 채팅방에서 제거
                    await sendbird_service.remove_member_from_channel(
                        channel_url=pod.chat_channel_url, user_id=str(user_id)
                    )

                except Exception as e:
                    logger.error(f"Sendbird 채팅방 멤버 제거 실패: {e}")

            # 모든 멤버를 데이터베이스에서 제거
            for member_id in member_ids:
                await self.crud.remove_pod_member(pod_id, member_id)
                logger.info(f"멤버 {member_id}를 파티에서 제거 완료")

            # 파티 상태를 CLOSED로 변경
            await self.crud.update_pod_status(pod_id, PodStatus.CLOSED)
            logger.info(f"파티 {pod_id} 상태를 CLOSED로 변경")

            return {
                "left": True,
                "is_owner": True,
                "members_removed": len(member_ids),
                "pod_status": "CLOSED",
            }

        else:
            # 일반 멤버가 나가는 경우 - 본인만 나가기
            logger.info(f"일반 멤버가 나가는 경우: pod_id={pod_id}, user_id={user_id}")

            # 멤버인지 확인
            is_member = await self.crud.is_pod_member(pod_id, user_id)
            if not is_member:
                logger.error(f"파티 멤버가 아님: pod_id={pod_id}, user_id={user_id}")
                raise_error("NO_POD_ACCESS_PERMISSION")

            # Sendbird 채팅방에서 제거
            if pod.chat_channel_url:
                try:
                    from app.services.sendbird_service import SendbirdService

                    sendbird_service = SendbirdService()

                    success = await sendbird_service.remove_member_from_channel(
                        channel_url=pod.chat_channel_url, user_id=str(user_id)
                    )

                    if success:
                        logger.info(f"사용자 {user_id}를 채팅방에서 제거 완료")
                    else:
                        logger.warning(f"사용자 {user_id} 채팅방 제거 실패")

                except Exception as e:
                    logger.error(f"Sendbird 채팅방 제거 실패: {e}")

            # 데이터베이스에서 멤버 제거
            await self.crud.remove_pod_member(pod_id, user_id)
            logger.info(f"사용자 {user_id}를 파티에서 제거 완료")

            return {
                "left": True,
                "is_owner": False,
                "members_removed": 1,
                "pod_status": pod.status.value,
            }

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
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        # TODO: 실제 total_count를 가져오는 로직 추가 필요
        total_count = len(pod_dtos)  # 임시로 현재 페이지 아이템 수 사용
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            size=size,
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
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            size=size,
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
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            size=size,
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
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        total_count = len(pod_dtos)
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            size=size,
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
        try:
            result = await self.crud.get_user_pods(user_id, page, size)
            pods = result["items"]
            total_count = result["total_count"]

            pod_dtos = []
            for pod in pods:
                try:
                    pod_dto = await self._enrich_pod_dto(pod, user_id)
                    pod_dtos.append(pod_dto)
                except Exception as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(f"Error processing pod {pod.id}: {str(e)}")
                    continue

            # PageDto 생성
            total_pages = math.ceil(total_count / size) if total_count > 0 else 0
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_user_pods: {str(e)}")
            raise

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=page,
            size=size,
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

    async def search_pods(
        self,
        user_id: Optional[int] = None,
        title: Optional[str] = None,
        main_category: Optional[str] = None,
        sub_category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        location: Optional[list[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageDto[PodDto]:
        """팟 검색"""
        result = await self.crud.search_pods(
            query=title or "",
            main_category=main_category,
            sub_categories=[sub_category] if sub_category else None,
            start_date=start_date,
            end_date=end_date,
            location=location[0] if location and len(location) > 0 else None,
            page=page,
            size=page_size,
        )

        # DTO 변환
        pod_dtos = []
        for pod in result["items"]:
            pod_dto = await self._convert_to_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        # PageDto 생성
        from app.schemas.common.page_dto import PageDto

        return PageDto[PodDto](
            items=pod_dtos,
            current_page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
            total_pages=result["total_pages"],
            has_next=result["page"] < result["total_pages"],
            has_prev=result["page"] > 1,
        )

    # - MARK: 사용자가 참여한 파티 조회
    async def get_user_joined_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 참여한 파티 목록 조회"""
        result = await self.crud.get_user_joined_pods(user_id, page, size)

        # DTO 변환
        pod_dtos = []
        for pod in result["items"]:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dtos.append(pod_dto)

        return PageDto(
            items=pod_dtos,
            current_page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
            total_pages=result["total_pages"],
            has_next=result["page"] < result["total_pages"],
            has_prev=result["page"] > 1,
        )

    # - MARK: 사용자가 좋아요한 파티 조회
    async def get_user_liked_pods(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodDto]:
        """사용자가 좋아요한 파티 목록 조회"""
        result = await self.crud.get_user_liked_pods(user_id, page, size)

        # DTO 변환
        pod_dtos = []
        for pod in result["items"]:
            pod_dto = await self._enrich_pod_dto(pod, user_id)
            pod_dto.is_liked = True  # 좋아요한 파티이므로 항상 True
            pod_dtos.append(pod_dto)

        return PageDto(
            items=pod_dtos,
            current_page=result["page"],
            size=result["page_size"],
            total_count=result["total_count"],
            total_pages=result["total_pages"],
            has_next=result["page"] < result["total_pages"],
            has_prev=result["page"] > 1,
        )

    async def _enrich_pod_dto(self, pod: Pod, user_id: Optional[int] = None) -> PodDto:
        """Pod를 PodDto로 변환하고 추가 정보를 설정"""
        from app.schemas.pod.pod_image_dto import PodImageDto

        # meeting_date와 meeting_time을 timestamp로 변환 (UTC로 저장된 값이므로 UTC로 해석)
        def _convert_to_timestamp(meeting_date, meeting_time):
            """date와 time 객체를 UTC로 해석하여 timestamp로 변환"""
            if meeting_date is None:
                return None
            from datetime import datetime, time as time_module, timezone

            if meeting_time is None:
                dt = datetime.combine(
                    meeting_date, time_module.min, tzinfo=timezone.utc
                )
            else:
                dt = datetime.combine(meeting_date, meeting_time, tzinfo=timezone.utc)
            timestamp_ms = int(dt.timestamp() * 1000)  # milliseconds

            # UTC 변환 확인 로그
            logger.info(
                f"[파티 조회] UTC timestamp 변환: pod_id={pod.id}, "
                f"DB 저장값(date={meeting_date}, time={meeting_time}), "
                f"UTC datetime={dt.isoformat()}, timestamp_ms={timestamp_ms}"
            )

            return timestamp_ms

        # 이미지 리스트 조회
        images_dto = []
        if hasattr(pod, "images") and pod.images:
            for img in sorted(pod.images, key=lambda x: x.display_order):
                images_dto.append(PodImageDto.model_validate(img))

        # PodDto를 수동으로 생성하여 applications 필드 접근 방지
        pod_dto = PodDto(
            id=pod.id,
            owner_id=pod.owner_id,
            title=pod.title,
            description=pod.description,
            image_url=pod.image_url,
            thumbnail_url=pod.thumbnail_url,
            sub_categories=pod.sub_categories,
            capacity=pod.capacity,
            place=pod.place,
            address=pod.address,
            sub_address=pod.sub_address,
            x=pod.x,
            y=pod.y,
            meeting_date=_convert_to_timestamp(pod.meeting_date, pod.meeting_time),
            selected_artist_id=pod.selected_artist_id,
            status=pod.status,
            chat_channel_url=pod.chat_channel_url,
            images=images_dto,
            created_at=pod.created_at,
            updated_at=pod.updated_at,
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
        pod_dto.joined_users_count = await self.crud.get_joined_users_count(pod.id)
        pod_dto.like_count = await self.crud.get_like_count(pod.id)
        pod_dto.view_count = await self.crud.get_view_count(pod.id)

        # 참여 중인 유저 목록 조회 (파티장 + 멤버들)
        from app.crud.pod.recruitment import RecruitmentCRUD
        from app.schemas.follow import SimpleUserDto

        recruitment_crud = RecruitmentCRUD(self.db)
        pod_members = await recruitment_crud.list_members(pod.id)

        # 차단된 유저 필터링 제거 (joined_users에서 모든 유저 표시)

        # PodMember를 SimpleUserDto로 변환
        joined_users = []

        # 1. 파티장 추가
        from app.models.tendency import UserTendencyResult
        from app.models.user import User

        # 파티장 정보 조회
        owner_result = await self.db.execute(
            select(User).where(User.id == pod.owner_id)
        )
        owner = owner_result.scalar_one_or_none()

        if owner:
            # 파티장 성향 타입 조회
            owner_tendency_result = await self.db.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == pod.owner_id
                )
            )
            owner_tendency = owner_tendency_result.scalar_one_or_none()
            owner_tendency_type = (
                owner_tendency.tendency_type if owner_tendency else None
            )

            owner_dto = SimpleUserDto(
                id=owner.id,
                nickname=owner.nickname,
                profile_image=owner.profile_image,
                intro=owner.intro,
                tendency_type=owner_tendency_type,
                is_following=False,
            )
            joined_users.append(owner_dto)

        # 2. 멤버들 추가
        for member in pod_members:

            # 성향 타입 조회
            result = await self.db.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == member.user_id
                )
            )
            user_tendency = result.scalar_one_or_none()
            tendency_type = user_tendency.tendency_type if user_tendency else None

            # User 정보 조회
            user = await self.db.get(User, member.user_id)

            if user:
                user_dto = SimpleUserDto(
                    id=user.id,
                    nickname=user.nickname,
                    profile_image=user.profile_image,
                    intro=user.intro,
                    tendency_type=tendency_type,
                    is_following=False,  # 필요 시 팔로우 여부 확인 로직 추가 가능
                )
                joined_users.append(user_dto)

        pod_dto.joined_users = joined_users

        # 사용자 정보가 있으면 개인화 필드 설정
        if user_id:
            pod_dto.is_liked = await self.crud.is_liked_by_user(pod.id, user_id)

            # 사용자의 신청서 정보 조회
            user_applications = await self.application_crud.get_applications_by_user_id(
                user_id
            )
            user_application = next(
                (app for app in user_applications if app.pod_id == pod.id), None
            )

            if user_application:
                # 신청한 사용자 정보 조회
                from app.models.user import User
                from app.schemas.follow import SimpleUserDto
                from app.models.tendency import UserTendencyResult

                app_user = await self.db.get(User, user_application.user_id)

                # 성향 타입 조회
                result = await self.db.execute(
                    select(UserTendencyResult).where(
                        UserTendencyResult.user_id == user_application.user_id
                    )
                )
                user_tendency = result.scalar_one_or_none()
                tendency_type = user_tendency.tendency_type if user_tendency else None

                if app_user:
                    user_dto = SimpleUserDto(
                        id=app_user.id,
                        nickname=app_user.nickname,
                        profile_image=app_user.profile_image,
                        intro=app_user.intro,
                        tendency_type=tendency_type,
                        is_following=False,
                    )

                    pod_dto.my_application = SimpleApplicationDto(
                        id=user_application.id,
                        user=user_dto,
                        status=user_application.status,
                        message=user_application.message,
                        applied_at=user_application.applied_at,  # int (Unix timestamp) 그대로 사용
                    )

        # 파티에 들어온 신청서 목록 조회
        applications = await self.application_crud.get_applications_by_pod_id(pod.id)

        application_dtos = []
        for app in applications:
            # 신청한 사용자 정보 조회
            from app.models.user import User
            from app.schemas.follow import SimpleUserDto
            from app.models.tendency import UserTendencyResult

            app_user = await self.db.get(User, app.user_id)

            # 성향 타입 조회
            result = await self.db.execute(
                select(UserTendencyResult).where(
                    UserTendencyResult.user_id == app.user_id
                )
            )
            user_tendency = result.scalar_one_or_none()
            tendency_type = user_tendency.tendency_type if user_tendency else None

            if app_user:
                user_dto = SimpleUserDto(
                    id=app_user.id,
                    nickname=app_user.nickname,
                    profile_image=app_user.profile_image,
                    intro=app_user.intro,
                    tendency_type=tendency_type,
                    is_following=False,
                )

                application_dto = SimpleApplicationDto(
                    id=app.id,
                    user=user_dto,
                    status=app.status,
                    message=app.message,
                    applied_at=app.applied_at,
                )
                application_dtos.append(application_dto)

        pod_dto.applications = application_dtos

        # 후기 목록 조회 및 추가
        reviews = await self.review_crud.get_all_reviews_by_pod(pod.id)
        from app.services.pod_review_service import PodReviewService

        review_service = PodReviewService(self.db)
        review_dtos = []
        for review in reviews:
            review_dto = await review_service._convert_to_dto(review)
            review_dtos.append(review_dto)

        pod_dto.reviews = review_dtos

        return pod_dto

    async def _convert_to_dto(self, pod: Pod, user_id: Optional[int] = None) -> PodDto:
        """Pod 엔터티를 PodDto로 변환"""
        return await self._enrich_pod_dto(pod, user_id)

    # - MARK: 파티 상태 업데이트 (알림 포함)
    async def update_pod_status_with_notification(
        self, pod_id: int, status: PodStatus
    ) -> bool:
        """파티 상태 업데이트 후 알림 전송"""
        pod = await self.crud.get_pod_by_id(pod_id)
        if not pod:
            return False

        # 파티 상태 업데이트
        pod.status = status
        await self.db.commit()

        try:
            # FCM 서비스 초기화
            fcm_service = FCMService()

            # 파티 참여자 목록 조회
            participants = await self.crud.get_pod_participants(pod_id)

            # 상태별 알림 전송
            if status == PodStatus.COMPLETED:
                # 파티 확정 알림 (모집 완료) - 파티장 제외 참여자에게 전송
                for participant in participants:
                    # 파티장 제외
                    if participant.id == pod.owner_id:
                        continue
                    try:
                        if participant.fcm_token:
                            await fcm_service.send_pod_confirmed(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod_id,
                                db=self.db,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                            logger.info(
                                f"파티 확정 알림 전송 성공: user_id={participant.id}, pod_id={pod_id}"
                            )
                        else:
                            logger.warning(
                                f"FCM 토큰이 없는 사용자: user_id={participant.id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"파티 확정 알림 전송 실패: user_id={participant.id}, error={e}"
                        )

            elif status == PodStatus.CANCELED:
                # 파티 취소 알림 - 파티장 제외 참여자에게 전송
                for participant in participants:
                    # 파티장 제외
                    if participant.id == pod.owner_id:
                        continue
                    try:
                        if participant.fcm_token:
                            await fcm_service.send_pod_canceled(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod_id,
                                db=self.db,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                            logger.info(
                                f"파티 취소 알림 전송 성공: user_id={participant.id}, pod_id={pod_id}"
                            )
                        else:
                            logger.warning(
                                f"FCM 토큰이 없는 사용자: user_id={participant.id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"파티 취소 알림 전송 실패: user_id={participant.id}, error={e}"
                        )

            elif status == PodStatus.CLOSED:
                # 파티 완료 알림
                for participant in participants:
                    try:
                        if participant.fcm_token:
                            await fcm_service.send_pod_completed(
                                token=participant.fcm_token,
                                party_name=pod.title,
                                pod_id=pod_id,
                                db=self.db,
                                user_id=participant.id,
                                related_user_id=pod.owner_id,
                            )
                            logger.info(
                                f"파티 완료 알림 전송 성공: user_id={participant.id}, pod_id={pod_id}"
                            )
                        else:
                            logger.warning(
                                f"FCM 토큰이 없는 사용자: user_id={participant.id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"파티 완료 알림 전송 실패: user_id={participant.id}, error={e}"
                        )

        except Exception as e:
            logger.error(f"파티 상태 업데이트 알림 처리 중 오류: {e}")

        return True
