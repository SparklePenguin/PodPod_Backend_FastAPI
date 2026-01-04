"""User State Service - 사용자 온보딩 상태 결정 로직"""

from app.features.users.models import User, UserState


class UserStateService:
    """사용자 온보딩 상태 결정 서비스"""

    @staticmethod
    def determine_state(
        user: User, has_preferred_artists: bool, has_tendency_result: bool
    ) -> UserState:
        """사용자 온보딩 상태 결정"""
        # 1. 선호 아티스트가 없으면 PREFERRED_ARTISTS
        if not has_preferred_artists:
            return UserState.PREFERRED_ARTISTS

        # 2. 성향 테스트 결과가 없으면 TENDENCY_TEST
        if not has_tendency_result:
            return UserState.TENDENCY_TEST

        # 3. 닉네임이 없으면 PROFILE_SETTING
        if not user.nickname:
            return UserState.PROFILE_SETTING

        # 4. 모든 조건을 만족하면 COMPLETED
        return UserState.COMPLETED
