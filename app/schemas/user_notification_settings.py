"""
사용자 알림 설정 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import time


class NotificationSettingsResponse(BaseModel):
    """알림 설정 응답"""

    notice_enabled: bool = Field(alias="noticeEnabled", description="공지 알림 활성화")
    pod_enabled: bool = Field(alias="podEnabled", description="파티 알림 활성화")
    community_enabled: bool = Field(
        alias="communityEnabled", description="커뮤니티 알림 활성화"
    )
    chat_enabled: bool = Field(alias="chatEnabled", description="채팅 알림 활성화")
    do_not_disturb_enabled: bool = Field(
        alias="doNotDisturbEnabled", description="방해금지 모드 활성화"
    )
    do_not_disturb_start: Optional[str] = Field(
        default=None,
        alias="doNotDisturbStart",
        description="방해금지 시작 시간 (HH:MM)",
    )
    do_not_disturb_end: Optional[str] = Field(
        default=None, alias="doNotDisturbEnd", description="방해금지 종료 시간 (HH:MM)"
    )
    marketing_enabled: bool = Field(
        alias="marketingEnabled", description="마케팅 알림 수신 동의"
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class UpdateNotificationSettingsRequest(BaseModel):
    """알림 설정 업데이트 요청"""

    notice_enabled: Optional[bool] = Field(default=None, alias="noticeEnabled")
    pod_enabled: Optional[bool] = Field(default=None, alias="podEnabled")
    community_enabled: Optional[bool] = Field(default=None, alias="communityEnabled")
    chat_enabled: Optional[bool] = Field(default=None, alias="chatEnabled")
    do_not_disturb_enabled: Optional[bool] = Field(
        default=None, alias="doNotDisturbEnabled"
    )
    do_not_disturb_start: Optional[str] = Field(
        default=None, alias="doNotDisturbStart", description="HH:MM 형식"
    )
    do_not_disturb_end: Optional[str] = Field(
        default=None, alias="doNotDisturbEnd", description="HH:MM 형식"
    )
    marketing_enabled: Optional[bool] = Field(default=None, alias="marketingEnabled")

    model_config = {
        "populate_by_name": True,
    }
