import sendbird_platform_sdk
from sendbird_platform_sdk.api import group_channel_api
from sendbird_platform_sdk.model.create_a_group_channel_request import (
    CreateAGroupChannelRequest,
)
from sendbird_platform_sdk.model.join_a_channel_request import JoinAChannelRequest
from sendbird_platform_sdk.model.leave_a_channel_request import LeaveAChannelRequest
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

    async def create_group_channel(
        self,
        channel_url: str,
        name: str,
        user_ids: List[str],
        cover_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        그룹 채팅방 생성

        Args:
            channel_url: 채널 URL (고유해야 함)
            name: 채널 이름
            user_ids: 참여자 사용자 ID 리스트
            cover_url: 커버 이미지 URL (선택사항)
            data: 추가 메타데이터 (선택사항)

        Returns:
            생성된 채널 정보 또는 None
        """
        try:
            with sendbird_platform_sdk.ApiClient(self.configuration) as api_client:
                api_instance = group_channel_api.GroupChannelApi(api_client)

                # CreateAGroupChannelRequest 객체 생성
                create_channel_request = CreateAGroupChannelRequest(
                    channel_url=channel_url,
                    name=name,
                    user_ids=user_ids,
                    is_distinct=False,  # 동일한 사용자들로 여러 채널 생성 가능
                    is_public=False,  # 비공개 채널
                    is_super=False,  # 일반 채널
                    is_ephemeral=False,  # 영구 채널
                )

                if cover_url:
                    create_channel_request.cover_url = cover_url

                if data:
                    create_channel_request.data = data

                # 채널 생성
                api_response = api_instance.create_a_group_channel(
                    api_token=self.api_token,
                    create_a_group_channel_request=create_channel_request,
                )

                return api_response.to_dict()

        except sendbird_platform_sdk.ApiException as e:
            print(f"Sendbird API 오류: {e.status} - {e.reason}")
            return None
        except Exception as e:
            print(f"Sendbird API 요청 실패: {e}")
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
