from app.common.schemas import BaseResponse, PageDto
from app.deps.auth import get_current_user_id
from app.deps.service import get_block_user_service
from app.features.users.schemas import BlockUserResponse, UserDto
from app.features.users.services.block_user_service import BlockUserService
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()


# - MARK: 사용자 차단
@router.post(
    "/{user_id}",
    response_model=BaseResponse[BlockUserResponse],
    description="사용자 차단 - 팔로우 관계도 함께 삭제됨",
)
async def block_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: BlockUserService = Depends(get_block_user_service),
):
    result = await service.block_user(current_user_id, user_id)
    return BaseResponse.ok(
        data=result,
        http_status=status.HTTP_200_OK,
        message_ko="사용자를 차단했습니다. 팔로우 관계도 해제되었습니다.",
        message_en="Successfully blocked the user. Follow relationship also removed.",
    )


# - MARK: 차단된 사용자 목록 조회
@router.get(
    "",
    response_model=BaseResponse[PageDto[UserDto]],
    description="차단된 사용자 목록 조회 (토큰 필요)",
)
async def get_blocked_users(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (1~100)"),
    current_user_id: int = Depends(get_current_user_id),
    service: BlockUserService = Depends(get_block_user_service),
):
    result = await service.get_blocked_users(current_user_id, page, size)
    return BaseResponse.ok(
        data=result,
        http_status=status.HTTP_200_OK,
        message_ko="차단된 사용자 목록을 조회했습니다.",
        message_en="Successfully retrieved blocked users list.",
    )


# - MARK: 사용자 차단 해제
@router.delete(
    "/{user_id}",
    response_model=BaseResponse[bool],
    description="사용자 차단 해제",
)
async def unblock_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: BlockUserService = Depends(get_block_user_service),
):
    await service.unblock_user(current_user_id, user_id)
    return BaseResponse.ok(
        data=True,
        http_status=status.HTTP_200_OK,
        message_ko="사용자 차단을 해제했습니다.",
        message_en="Successfully unblocked the user.",
    )
