import sendbird_platform_sdk
import json
from sendbird_platform_sdk.api import group_channel_api
from sendbird_platform_sdk.model.create_a_group_channel_request import (
    CreateAGroupChannelRequest,
)
from sendbird_platform_sdk.model.join_a_channel_request import JoinAChannelRequest
from sendbird_platform_sdk.model.leave_a_channel_request import LeaveAChannelRequest
from sendbird_platform_sdk.model.sendbird_user import SendbirdUser
from typing import Optional, Dict, Any, List
from app.core.config import settings


class SendbirdService:
    """Sendbird API 서비스 (공식 SDK 사용)"""

    def __init__(self):
        if not settings.SENDBIRD_APP_ID or not settings.SENDBIRD_API_TOKEN:
            raise ValueError(
                "Sendbird 설정이 누락되었습니다. "
                "SENDBIRD_APP_ID와 SENDBIRD_API_TOKEN 환경변수를 설정해주세요."
            )

        self.configuration = sendbird_platform_sdk.Configuration(
            host=f"https://api-{settings.SENDBIRD_APP_ID}.sendbird.com"
        )
        self.api_token = settings.SENDBIRD_API_TOKEN

    async def create_group_channel_with_join(
        self,
        channel_url: str,
        name: str,
        user_ids: List[str],
        cover_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        user_profiles: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        그룹 채팅방 생성 (join_by_user_id: true 옵션 포함)

        Args:
            channel_url: 채널 URL (고유해야 함)
            name: 채널 이름
            user_ids: 참여자 사용자 ID 리스트
            cover_url: 커버 이미지 URL (선택사항)
            data: 추가 메타데이터 (선택사항)
            user_profiles: 사용자별 프로필 정보 {user_id: {"nickname": "...", "profile_url": "..."}} (선택사항)

        Returns:
            생성된 채널 정보 또는 None
        """
        try:
            import httpx
            import json

            # 원시 HTTP 요청으로 채널 생성 (join_by_user_id: true 옵션 포함)
            from app.core.config import settings

            url = (
                f"https://api-{settings.SENDBIRD_APP_ID}.sendbird.com/v3/group_channels"
            )
            headers = {"Api-Token": self.api_token, "Content-Type": "application/json"}

            # 채널 생성 payload
            payload = {
                "user_ids": user_ids,
                "is_public": False,  # 비공개 채널
                "join_by_user_id": True,  # 핵심 옵션!
                "name": name,
                "channel_url": channel_url,
            }

            if cover_url:
                payload["cover_url"] = cover_url

            if data:
                payload["data"] = json.dumps(data)

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    return response.json()
                else:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Sendbird 채널 생성 실패: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Sendbird 채널 생성 실패: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None

    async def create_group_channel(
        self,
        channel_url: str,
        name: str,
        user_ids: List[str],
        cover_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        user_profiles: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        그룹 채팅방 생성

        Args:
            channel_url: 채널 URL (고유해야 함)
            name: 채널 이름
            user_ids: 참여자 사용자 ID 리스트
            cover_url: 커버 이미지 URL (선택사항)
            data: 추가 메타데이터 (선택사항)
            user_profiles: 사용자별 프로필 정보 {user_id: {"nickname": "...", "profile_url": "..."}} (선택사항)

        Returns:
            생성된 채널 정보 또는 None
        """
        try:
            with sendbird_platform_sdk.ApiClient(self.configuration) as api_client:
                api_instance = group_channel_api.GroupChannelApi(api_client)

                # SendbirdUser 객체들 생성 (프로필 정보 포함)
                users = []
                for user_id in user_ids:
                    user_kwargs = {"user_id": user_id}
                    if user_profiles and user_id in user_profiles:
                        profile = user_profiles[user_id]
                        if "nickname" in profile:
                            user_kwargs["nickname"] = profile["nickname"]
                        if "profile_url" in profile:
                            user_kwargs["profile_url"] = profile["profile_url"]
                    users.append(SendbirdUser(**user_kwargs))

                # CreateAGroupChannelRequest 객체 생성
                create_channel_request = CreateAGroupChannelRequest(
                    users=users,
                    channel_url=channel_url,
                    name=name,
                    is_distinct=False,  # 동일한 사용자들로 여러 채널 생성 가능
                    is_public=False,  # 비공개 채널
                    is_super=False,  # 일반 채널
                    is_ephemeral=False,  # 영구 채널
                )

                if cover_url:
                    create_channel_request.cover_url = cover_url

                if data:
                    import json

                    create_channel_request.data = json.dumps(data)

                # 채널 생성
                api_response = api_instance.create_a_group_channel(
                    api_token=self.api_token,
                    create_a_group_channel_request=create_channel_request,
                    _check_return_type=False,  # SDK validation 비활성화
                )

                # 응답이 dict면 그대로 반환, 아니면 to_dict() 시도
                if isinstance(api_response, dict):
                    return api_response
                elif hasattr(api_response, "to_dict"):
                    return api_response.to_dict()
                else:
                    # 최소한의 정보라도 반환
                    return {"channel_url": channel_url}

        except sendbird_platform_sdk.ApiException as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Sendbird API 오류: {e.status} - {e.reason}")
            logger.error(f"오류 상세: {e.body}")
            return None
        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Sendbird API 요청 실패: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None

    async def get_channel_metadata(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """
        채널 메타데이터 조회

        Args:
            channel_url: 채널 URL

        Returns:
            채널 메타데이터 또는 None
        """
        try:
            print(f"채널 메타데이터 조회 시도: {channel_url}")

            # 원시 HTTP 요청으로 직접 처리
            import httpx

            url = f"https://api-{settings.SENDBIRD_APP_ID}.sendbird.com/v3/group_channels/{channel_url}"
            headers = {"Api-Token": self.api_token, "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    print(f"채널 메타데이터 조회 성공: {result}")
                    return result
                else:
                    print(
                        f"Sendbird API 오류: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            print(f"Sendbird API 요청 실패: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def update_channel_metadata(
        self, channel_url: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        채널 메타데이터 업데이트

        Args:
            channel_url: 채널 URL
            data: 업데이트할 메타데이터

        Returns:
            업데이트된 채널 정보 또는 None
        """
        try:
            print(f"채널 메타데이터 업데이트 시도: {channel_url}")

            # 원시 HTTP 요청으로 직접 처리
            import httpx

            url = f"https://api-{settings.SENDBIRD_APP_ID}.sendbird.com/v3/group_channels/{channel_url}"
            headers = {"Api-Token": self.api_token, "Content-Type": "application/json"}

            # 업데이트할 데이터 준비 (이미 JSON 문자열로 받음)
            update_data = {"data": data}

            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=headers, json=update_data)

                if response.status_code == 200:
                    result = response.json()
                    print(f"채널 메타데이터 업데이트 성공: {result}")
                    return result
                else:
                    print(
                        f"Sendbird API 오류: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            print(f"Sendbird API 요청 실패: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def add_members_to_channel(
        self, channel_url: str, user_ids: List[str]
    ) -> bool:
        """
        채널에 멤버 추가

        Args:
            channel_url: 채널 URL
            user_ids: 추가할 사용자 ID 리스트

        Returns:
            성공 여부
        """
        try:
            with sendbird_platform_sdk.ApiClient(self.configuration) as api_client:
                api_instance = group_channel_api.GroupChannelApi(api_client)

                # JoinAChannelRequest 객체 생성
                join_channel_request = JoinAChannelRequest(user_ids=user_ids)

                # 멤버 추가
                api_response = api_instance.join_a_channel(
                    api_token=self.api_token,
                    channel_url=channel_url,
                    join_a_channel_request=join_channel_request,
                )

                return True

        except sendbird_platform_sdk.ApiException as e:
            print(f"Sendbird 멤버 추가 오류: {e.status} - {e.reason}")
            return False
        except Exception as e:
            print(f"Sendbird 멤버 추가 실패: {e}")
            return False

    async def remove_member_from_channel(self, channel_url: str, user_id: str) -> bool:
        """
        채널에서 멤버 제거

        Args:
            channel_url: 채널 URL
            user_id: 제거할 사용자 ID

        Returns:
            성공 여부
        """
        try:
            with sendbird_platform_sdk.ApiClient(self.configuration) as api_client:
                api_instance = group_channel_api.GroupChannelApi(api_client)

                # LeaveAChannelRequest 객체 생성
                leave_channel_request = LeaveAChannelRequest(user_ids=[user_id])

                # 멤버 제거
                api_response = api_instance.leave_a_channel(
                    api_token=self.api_token,
                    channel_url=channel_url,
                    leave_a_channel_request=leave_channel_request,
                )

                return True

        except sendbird_platform_sdk.ApiException as e:
            print(f"Sendbird 멤버 제거 오류: {e.status} - {e.reason}")
            return False
        except Exception as e:
            print(f"Sendbird 멤버 제거 실패: {e}")
            return False

    async def delete_channel(self, channel_url: str) -> bool:
        """
        채널 삭제

        Args:
            channel_url: 채널 URL

        Returns:
            성공 여부
        """
        try:
            with sendbird_platform_sdk.ApiClient(self.configuration) as api_client:
                api_instance = group_channel_api.GroupChannelApi(api_client)

                # 채널 삭제
                api_response = api_instance.delete_a_group_channel(
                    api_token=self.api_token, channel_url=channel_url
                )

                return True

        except sendbird_platform_sdk.ApiException as e:
            print(f"Sendbird 채널 삭제 오류: {e.status} - {e.reason}")
            return False
        except Exception as e:
            print(f"Sendbird 채널 삭제 실패: {e}")
            return False

    async def join_channel(self, channel_url: str, user_ids: List[str]) -> bool:
        """
        채널에 사용자 참여 (PUT 방식)
        Args:
            channel_url: 채널 URL
            user_ids: 참여할 사용자 ID 리스트
        Returns:
            성공 여부
        """
        try:
            import httpx

            from app.core.config import settings

            url = f"https://api-{settings.SENDBIRD_APP_ID}.sendbird.com/v3/group_channels/{channel_url}/join"
            headers = {"Api-Token": self.api_token, "Content-Type": "application/json"}

            # 각 사용자별로 join 요청
            for user_id in user_ids:
                data = {"user_id": user_id}

                async with httpx.AsyncClient() as client:
                    response = await client.put(url, headers=headers, json=data)

                    if response.status_code != 200:
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.error(
                            f"Sendbird join 실패 (userId: {user_id}): {response.status_code} - {response.text}"
                        )
                        return False

            return True

        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Sendbird join 실패: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
