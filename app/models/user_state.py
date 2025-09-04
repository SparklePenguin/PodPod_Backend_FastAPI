from enum import Enum


class UserState(str, Enum):
    """사용자 온보딩 상태"""
    PREFERRED_ARTISTS = "PREFERRED_ARTISTS"  # 선호 아티스트 설정 필요
    TENDENCY_TEST = "TENDENCY_TEST"          # 성향 테스트 필요
    PROFILE_SETTING = "PROFILE_SETTING"      # 프로필 설정 필요
    COMPLETED = "COMPLETED"                  # 온보딩 완료