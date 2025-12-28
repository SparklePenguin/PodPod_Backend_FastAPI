import json
from datetime import datetime

from app.common.schemas import BaseResponse
from app.core.database import get_session
from app.core.services.sendbird_service import SendbirdService
from app.features.pods.repositories.pod_repository import PodRepository
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# - MARK: Sendbird 채팅방 생성
@router.post("/create-channels")
async def create_sendbird_channels(db: AsyncSession = Depends(get_session)):
    """모든 파티에 Sendbird 채팅방 생성"""
    try:
        pod_crud = PodRepository(db)

        # Sendbird 서비스 초기화
        try:
            sendbird_service = SendbirdService()
        except ValueError:
            return BaseResponse.error(
                error_key="SENDBIRD_CONFIG_ERROR",
                error_code=1001,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="Sendbird 설정이 누락되었습니다. SENDBIRD_APP_ID와 SENDBIRD_API_TOKEN을 설정해주세요.",
                message_en="Sendbird configuration is missing. Please set SENDBIRD_APP_ID and SENDBIRD_API_TOKEN.",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="SENDBIRD_SERVICE_ERROR",
                error_code=1002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko=f"Sendbird 서비스 초기화 실패: {str(e)}",
                message_en=f"Failed to initialize Sendbird service: {str(e)}",
            )

        # 모든 파티 조회
        pods = await pod_crud.get_all_pods()

        if not pods:
            return BaseResponse.ok(
                data={
                    "message": "생성할 파티가 없습니다.",
                    "success_count": 0,
                    "error_count": 0,
                },
                http_status=status.HTTP_200_OK,
            )

        success_count = 0
        error_count = 0
        results = []

        for pod in pods:
            try:
                # Pod 속성들을 안전하게 가져오기
                pod_id: int = getattr(pod, "id", 0)
                pod_title: str = getattr(pod, "title", "")
                pod_owner_id: int = getattr(pod, "owner_id", 0)
                pod_thumbnail_url: str | None = getattr(pod, "thumbnail_url", None)
                pod_place: str | None = getattr(pod, "place", None)

                # 채널 URL 생성 (pod_{pod_id}_chat 형식)
                channel_url = f"pod_{pod_id}_chat"

                # 이미 채팅방이 있는지 확인
                chat_channel_url: str | None = getattr(pod, "chat_channel_url", None)
                if chat_channel_url:
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod_id,
                            "title": pod_title,
                            "channel_url": chat_channel_url,
                            "status": "already_exists",
                        }
                    )
                    continue

                # Sendbird 채팅방 생성
                channel_data = await sendbird_service.create_group_channel(
                    channel_url=channel_url,
                    name=f"{pod_title} 채팅방",
                    user_ids=[str(pod_owner_id)],  # 파티 생성자만 초기 멤버
                    data={
                        "id": pod_id,
                        "ownerId": pod_owner_id,
                        "title": pod_title,
                        "thumbnailUrl": pod_thumbnail_url or "",
                        "meetingPlace": pod_place or "",
                        "meetingDate": (
                            int(
                                datetime.combine(meeting_date, meeting_time).timestamp()
                                * 1000
                            )
                            if (meeting_date := getattr(pod, "meeting_date", None))
                            and (meeting_time := getattr(pod, "meeting_time", None))
                            else 0
                        ),
                        "subCategories": (
                            json.loads(sub_categories)
                            if (sub_categories := getattr(pod, "sub_categories", None))
                            else []
                        ),
                    },
                )

                if channel_data:
                    # 데이터베이스에 채팅방 URL 저장
                    await pod_crud.update_chat_channel_url(pod_id, channel_url)
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod_id,
                            "title": pod_title,
                            "channel_url": channel_url,
                            "status": "created",
                        }
                    )
                else:
                    error_count += 1
                    results.append(
                        {
                            "pod_id": pod_id,
                            "title": pod_title,
                            "channel_url": channel_url,
                            "status": "failed",
                            "error": "Sendbird 채팅방 생성 실패",
                        }
                    )

            except Exception as e:
                pod_id: int = getattr(pod, "id", 0)
                pod_title: str = getattr(pod, "title", "")
                error_count += 1
                results.append(
                    {
                        "pod_id": pod_id,
                        "title": pod_title,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return BaseResponse.ok(
            data={
                "message": f"채팅방 생성 완료: 성공 {success_count}개, 실패 {error_count}개",
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            },
            http_status=status.HTTP_200_OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )


# - MARK: Sendbird 채팅방 삭제
@router.delete("/delete-channels")
async def delete_sendbird_channels(db: AsyncSession = Depends(get_session)):
    """모든 Sendbird 채팅방 삭제"""
    try:
        pod_crud = PodRepository(db)

        # Sendbird 서비스 초기화
        try:
            sendbird_service = SendbirdService()
        except ValueError:
            return BaseResponse.error(
                error_key="SENDBIRD_CONFIG_ERROR",
                error_code=1001,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="Sendbird 설정이 누락되었습니다.",
                message_en="Sendbird configuration is missing.",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="SENDBIRD_SERVICE_ERROR",
                error_code=1002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko=f"Sendbird 서비스 초기화 실패: {str(e)}",
                message_en=f"Failed to initialize Sendbird service: {str(e)}",
            )

        # 채팅방 URL이 있는 파티들 조회
        pods_with_channels = await pod_crud.get_pods_with_chat_channels()

        if not pods_with_channels:
            return BaseResponse.ok(
                data={
                    "message": "삭제할 채팅방이 없습니다.",
                    "success_count": 0,
                    "error_count": 0,
                },
                http_status=status.HTTP_200_OK,
            )

        success_count = 0
        error_count = 0
        results = []

        for pod in pods_with_channels:
            try:
                # Sendbird 채팅방 삭제
                chat_channel_url: str | None = getattr(pod, "chat_channel_url", None)
                if not chat_channel_url:
                    continue
                success = await sendbird_service.delete_channel(chat_channel_url)

                if success:
                    # 데이터베이스에서 채팅방 URL 제거
                    pod_id: int = getattr(pod, "id", 0)
                    await pod_crud.update_chat_channel_url(pod_id, None)
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": chat_channel_url,
                            "status": "success",
                        }
                    )
                else:
                    error_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": chat_channel_url,
                            "status": "failed",
                            "error": "Sendbird 채팅방 삭제 실패",
                        }
                    )

            except Exception as e:
                error_count += 1
                results.append(
                    {
                        "pod_id": pod.id,
                        "title": pod.title,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return BaseResponse.ok(
            data={
                "message": f"채팅방 삭제 완료: 성공 {success_count}개, 실패 {error_count}개",
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            },
            http_status=status.HTTP_200_OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )


# - MARK: Sendbird 채팅방 상태 확인
@router.get("/check-channels")
async def check_sendbird_channels(db: AsyncSession = Depends(get_session)):
    """채팅방 상태 확인"""
    try:
        pod_crud = PodRepository(db)

        # 모든 파티 조회
        pods = await pod_crud.get_all_pods()

        if not pods:
            return BaseResponse.ok(
                data={"message": "파티가 없습니다.", "pods": []},
                http_status=status.HTTP_200_OK,
            )

        results = []
        total_pods = len(pods)
        pods_with_channels = 0
        pods_without_channels = 0

        for pod in pods:
            pod_id: int = getattr(pod, "id", 0)
            pod_title: str = getattr(pod, "title", "")
            chat_channel_url: str | None = getattr(pod, "chat_channel_url", None)
            has_channel = chat_channel_url is not None
            if has_channel:
                pods_with_channels += 1
            else:
                pods_without_channels += 1

            results.append(
                {
                    "pod_id": pod_id,
                    "title": pod_title,
                    "has_channel": has_channel,
                    "channel_url": chat_channel_url,
                }
            )

        return BaseResponse.ok(
            data={
                "message": f"총 {total_pods}개 파티: 채팅방 있음 {pods_with_channels}개, 없음 {pods_without_channels}개",
                "total_pods": total_pods,
                "pods_with_channels": pods_with_channels,
                "pods_without_channels": pods_without_channels,
                "pods": results,
            },
            http_status=status.HTTP_200_OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )


# - MARK: Sendbird 채널 메타데이터 조회
@router.get("/channel-metadata/{channel_url}")
async def get_channel_metadata(
    channel_url: str, db: AsyncSession = Depends(get_session)
):
    """채널 메타데이터 확인"""
    try:
        # Sendbird 서비스 초기화
        try:
            sendbird_service = SendbirdService()
        except ValueError:
            return BaseResponse.error(
                error_key="SENDBIRD_CONFIG_ERROR",
                error_code=1001,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="Sendbird 설정이 누락되었습니다.",
                message_en="Sendbird configuration is missing.",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="SENDBIRD_SERVICE_ERROR",
                error_code=1002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko=f"Sendbird 서비스 초기화 실패: {str(e)}",
                message_en=f"Failed to initialize Sendbird service: {str(e)}",
            )

        metadata = await sendbird_service.get_channel_metadata(channel_url)

        if metadata:
            return BaseResponse.ok(
                data={"channel_url": channel_url, "metadata": metadata},
                http_status=status.HTTP_200_OK,
            )
        else:
            return BaseResponse.error(
                error_key="CHANNEL_NOT_FOUND",
                error_code=404,
                http_status=status.HTTP_404_NOT_FOUND,
                message_ko="채널을 찾을 수 없습니다",
                message_en="Channel not found",
            )

    except Exception:
        return BaseResponse.error(
            error_key="METADATA_FETCH_FAILED",
            error_code=500,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko="메타데이터 조회 실패",
            message_en="Failed to fetch metadata",
        )


# - MARK: Sendbird 채널 메타데이터 업데이트
@router.put("/update-metadata")
async def update_channel_metadata(db: AsyncSession = Depends(get_session)):
    """기존 채팅방들의 메타데이터 업데이트"""
    try:
        pod_crud = PodRepository(db)

        # Sendbird 서비스 초기화
        try:
            sendbird_service = SendbirdService()
        except ValueError:
            return BaseResponse.error(
                error_key="SENDBIRD_CONFIG_ERROR",
                error_code=1001,
                http_status=status.HTTP_400_BAD_REQUEST,
                message_ko="Sendbird 설정이 누락되었습니다.",
                message_en="Sendbird configuration is missing.",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="SENDBIRD_SERVICE_ERROR",
                error_code=1002,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message_ko=f"Sendbird 서비스 초기화 실패: {str(e)}",
                message_en=f"Failed to initialize Sendbird service: {str(e)}",
            )

        # 채팅방 URL이 있는 파티들 조회
        pods_with_channels = await pod_crud.get_pods_with_chat_channels()

        if not pods_with_channels:
            return BaseResponse.ok(
                data={"message": "업데이트할 채팅방이 없습니다."},
                http_status=status.HTTP_200_OK,
            )

        success_count = 0
        error_count = 0
        results = []

        for pod in pods_with_channels:
            try:
                # Pod 속성들을 안전하게 가져오기
                pod_id: int = getattr(pod, "id", 0)
                pod_title: str = getattr(pod, "title", "")
                pod_owner_id: int = getattr(pod, "owner_id", 0)
                pod_thumbnail_url: str | None = getattr(pod, "thumbnail_url", None)
                pod_place: str | None = getattr(pod, "place", None)

                # 새로운 메타데이터 생성
                new_metadata = {
                    "id": pod_id,
                    "ownerId": pod_owner_id,
                    "title": pod_title,
                    "thumbnailUrl": pod_thumbnail_url or "",
                    "meetingPlace": pod_place or "",
                    "meetingDate": (
                        int(
                            datetime.combine(meeting_date, meeting_time).timestamp()
                            * 1000
                        )
                        if (meeting_date := getattr(pod, "meeting_date", None))
                        and (meeting_time := getattr(pod, "meeting_time", None))
                        else 0
                    ),
                    "subCategories": (
                        json.loads(sub_categories)
                        if (sub_categories := getattr(pod, "sub_categories", None))
                        else []
                    ),
                }

                # Sendbird 채널 메타데이터 업데이트
                chat_channel_url: str | None = getattr(pod, "chat_channel_url", None)
                if not chat_channel_url:
                    continue
                update_result = await sendbird_service.update_channel_metadata(
                    chat_channel_url, new_metadata
                )

                if update_result:
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod_id,
                            "title": pod_title,
                            "channel_url": chat_channel_url,
                            "status": "updated",
                        }
                    )
                else:
                    error_count += 1
                    results.append(
                        {
                            "pod_id": pod_id,
                            "title": pod_title,
                            "channel_url": chat_channel_url,
                            "status": "failed",
                            "error": "메타데이터 업데이트 실패",
                        }
                    )

            except Exception as e:
                pod_id: int = getattr(pod, "id", 0)
                pod_title: str = getattr(pod, "title", "")
                error_count += 1
                results.append(
                    {
                        "pod_id": pod_id,
                        "title": pod_title,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return BaseResponse.ok(
            data={
                "message": f"메타데이터 업데이트 완료: 성공 {success_count}개, 실패 {error_count}개",
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            },
            http_status=status.HTTP_200_OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )
