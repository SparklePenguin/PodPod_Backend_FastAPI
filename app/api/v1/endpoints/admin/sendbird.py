from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import get_db
from app.crud.pod.pod import PodCRUD
from app.services.sendbird_service import SendbirdService
from app.schemas.common.base_response import BaseResponse
from app.core.http_status import HttpStatus
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/create-channels")
async def create_sendbird_channels(db: AsyncSession = Depends(get_db)):
    """모든 파티에 Sendbird 채팅방 생성"""
    try:
        pod_crud = PodCRUD(db)

        # Sendbird 서비스 초기화
        try:
            sendbird_service = SendbirdService()
        except ValueError as e:
            return BaseResponse.error(
                error_key="SENDBIRD_CONFIG_ERROR",
                error_code=1001,
                http_status=HttpStatus.BAD_REQUEST,
                message_ko="Sendbird 설정이 누락되었습니다. SENDBIRD_APP_ID와 SENDBIRD_API_TOKEN을 설정해주세요.",
                message_en="Sendbird configuration is missing. Please set SENDBIRD_APP_ID and SENDBIRD_API_TOKEN.",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="SENDBIRD_SERVICE_ERROR",
                error_code=1002,
                http_status=HttpStatus.INTERNAL_SERVER_ERROR,
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
                http_status=HttpStatus.OK,
            )

        success_count = 0
        error_count = 0
        results = []

        for pod in pods:
            try:
                # 채널 URL 생성 (pod_{pod_id}_chat 형식)
                channel_url = f"pod_{pod.id}_chat"

                # 이미 채팅방이 있는지 확인
                if pod.chat_channel_url:
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": pod.chat_channel_url,
                            "status": "already_exists",
                        }
                    )
                    continue

                # Sendbird 채팅방 생성
                channel_data = await sendbird_service.create_group_channel(
                    channel_url=channel_url,
                    name=f"{pod.title} 채팅방",
                    user_ids=[str(pod.owner_id)],  # 파티 생성자만 초기 멤버
                    data={"pod_id": pod.id, "pod_title": pod.title, "type": "pod_chat"},
                )

                if channel_data:
                    # 데이터베이스에 채팅방 URL 저장
                    await pod_crud.update_chat_channel_url(pod.id, channel_url)
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": channel_url,
                            "status": "created",
                        }
                    )
                else:
                    error_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": channel_url,
                            "status": "failed",
                            "error": "Sendbird 채팅방 생성 실패",
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
                "message": f"채팅방 생성 완료: 성공 {success_count}개, 실패 {error_count}개",
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            },
            http_status=HttpStatus.OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )


@router.delete("/delete-channels")
async def delete_sendbird_channels(db: AsyncSession = Depends(get_db)):
    """모든 Sendbird 채팅방 삭제"""
    try:
        pod_crud = PodCRUD(db)

        # Sendbird 서비스 초기화
        try:
            sendbird_service = SendbirdService()
        except ValueError as e:
            return BaseResponse.error(
                error_key="SENDBIRD_CONFIG_ERROR",
                error_code=1001,
                http_status=HttpStatus.BAD_REQUEST,
                message_ko="Sendbird 설정이 누락되었습니다.",
                message_en="Sendbird configuration is missing.",
            )
        except Exception as e:
            return BaseResponse.error(
                error_key="SENDBIRD_SERVICE_ERROR",
                error_code=1002,
                http_status=HttpStatus.INTERNAL_SERVER_ERROR,
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
                http_status=HttpStatus.OK,
            )

        success_count = 0
        error_count = 0
        results = []

        for pod in pods_with_channels:
            try:
                # Sendbird 채팅방 삭제
                success = await sendbird_service.delete_channel(pod.chat_channel_url)

                if success:
                    # 데이터베이스에서 채팅방 URL 제거
                    await pod_crud.update_chat_channel_url(pod.id, None)
                    success_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": pod.chat_channel_url,
                            "status": "success",
                        }
                    )
                else:
                    error_count += 1
                    results.append(
                        {
                            "pod_id": pod.id,
                            "title": pod.title,
                            "channel_url": pod.chat_channel_url,
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
            http_status=HttpStatus.OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )


@router.get("/check-channels")
async def check_sendbird_channels(db: AsyncSession = Depends(get_db)):
    """채팅방 상태 확인"""
    try:
        pod_crud = PodCRUD(db)

        # 모든 파티 조회
        pods = await pod_crud.get_all_pods()

        if not pods:
            return BaseResponse.ok(
                data={"message": "파티가 없습니다.", "pods": []},
                http_status=HttpStatus.OK,
            )

        results = []
        total_pods = len(pods)
        pods_with_channels = 0
        pods_without_channels = 0

        for pod in pods:
            has_channel = pod.chat_channel_url is not None
            if has_channel:
                pods_with_channels += 1
            else:
                pods_without_channels += 1

            results.append(
                {
                    "pod_id": pod.id,
                    "title": pod.title,
                    "has_channel": has_channel,
                    "channel_url": pod.chat_channel_url,
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
            http_status=HttpStatus.OK,
        )

    except Exception as e:
        return BaseResponse.error(
            error_key="INTERNAL_SERVER_ERROR",
            error_code=5000,
            http_status=HttpStatus.INTERNAL_SERVER_ERROR,
            message_ko=f"서버 오류: {str(e)}",
            message_en=f"Internal server error: {str(e)}",
        )
