from app.common.schemas import BaseResponse
from app.features.users.routers._base import UserCommonController


class UserCommonRouter:

    @staticmethod
    @UserCommonController.ROUTER.get(
        "/types",
        response_model=BaseResponse[dict],
        description="사용자 조회 가능한 타입 목록",
    )
    async def get_user_types():
        """사용 가능한 사용자 조회 타입 목록"""
        types = {
            "types": [
                {
                    "value": "recommended",
                    "label_ko": "추천 사용자",
                    "label_en": "Recommended Users",
                    "description_ko": "추천 사용자 목록",
                    "description_en": "List of recommended users",
                },
                {
                    "value": "followings",
                    "label_ko": "팔로우하는 사용자",
                    "label_en": "Following Users",
                    "description_ko": "내가 팔로우하는 사용자 목록",
                    "description_en": "List of users I follow",
                },
                {
                    "value": "followers",
                    "label_ko": "팔로워",
                    "label_en": "Followers",
                    "description_ko": "나를 팔로우하는 사용자 목록",
                    "description_en": "List of users who follow me",
                },
                {
                    "value": "blocks",
                    "label_ko": "차단된 사용자",
                    "label_en": "Blocked Users",
                    "description_ko": "차단한 사용자 목록",
                    "description_en": "List of blocked users",
                },
            ]
        }
        return BaseResponse.ok(
            data=types,
            message_ko="사용자 조회 타입 목록을 조회했습니다.",
            message_en="Successfully retrieved user types.",
        )
