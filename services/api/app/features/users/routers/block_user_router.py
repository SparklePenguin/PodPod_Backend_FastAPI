from fastapi import APIRouter, Depends, status

from app.common.schemas import BaseResponse
from app.deps.auth import get_current_user_id
from app.deps.providers import get_block_user_use_case
from app.features.users.routers import UserRouterRootLabel
from app.features.users.routers._base import BlockUserRouterLabel
from app.features.users.schemas import BlockInfoDto
from app.features.users.use_cases.block_user_use_case import BlockUserUseCase


class BlockUserRouter:
    router = APIRouter(prefix=f"{UserRouterRootLabel.PREFIX}", tags=[BlockUserRouterLabel.TAG])

    @staticmethod
    @router.post(
        f"{BlockUserRouterLabel.PREFIX}" + "/{user_id}",
        response_model=BaseResponse[BlockInfoDto],
        description="사용자 차단 - 팔로우 관계도 함께 삭제됨",
    )
    async def block_user(
            user_id: int,
            current_user_id: int = Depends(get_current_user_id),
            use_case: BlockUserUseCase = Depends(get_block_user_use_case),
    ):
        result = await use_case.block_user(current_user_id, user_id)
        return BaseResponse.ok(
            data=result,
            http_status=status.HTTP_200_OK,
            message_ko="사용자를 차단했습니다. 팔로우 관계도 해제되었습니다.",
            message_en="Successfully blocked the user. Follow relationship also removed.",
        )

    @staticmethod
    @router.delete(
        f"{BlockUserRouterLabel.PREFIX}" + "/{user_id}",
        response_model=BaseResponse[bool],
        description="사용자 차단 해제",
    )
    async def unblock_user(
            user_id: int,
            current_user_id: int = Depends(get_current_user_id),
            use_case: BlockUserUseCase = Depends(get_block_user_use_case),
    ):
        await use_case.unblock_user(current_user_id, user_id)
        return BaseResponse.ok(
            data=True,
            http_status=status.HTTP_200_OK,
            message_ko="사용자 차단을 해제했습니다.",
            message_en="Successfully unblocked the user.",
        )
