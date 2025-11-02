from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.pod_review import PodReviewCRUD
from app.crud.pod.pod import PodCRUD
from app.crud.user import UserCRUD
from app.schemas.pod_review import (
    PodReviewCreateRequest,
    PodReviewUpdateRequest,
    PodReviewDto,
    SimplePodDto,
)
from app.schemas.follow import SimpleUserDto
from app.schemas.common import PageDto
from app.models.pod_review import PodReview
from app.models.user import User
from app.core.logging_config import get_logger
from app.services.fcm_service import FCMService
from sqlalchemy import select
from datetime import datetime, timezone, date, time
import math

logger = get_logger("pod_review_service")


def _convert_to_combined_timestamp(meeting_date, meeting_time):
    """date와 time 객체를 하나의 timestamp로 변환"""
    if meeting_date is None:
        return None
    if meeting_time is None:
        # time이 없으면 date만 사용 (00:00:00)
        dt = datetime.combine(meeting_date, time.min)
    else:
        # date와 time을 결합
        dt = datetime.combine(meeting_date, meeting_time)
    return int(dt.timestamp() * 1000)  # milliseconds


class PodReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = PodReviewCRUD(db)
        self.pod_crud = PodCRUD(db)
        self.user_crud = UserCRUD(db)

    async def create_review(
        self, user_id: int, request: PodReviewCreateRequest
    ) -> Optional[PodReviewDto]:
        """후기 생성"""
        try:
            # 이미 작성한 후기가 있는지 확인
            existing_review = await self.crud.get_review_by_pod_and_user(
                request.pod_id, user_id
            )
            if existing_review:
                raise ValueError("이미 해당 파티에 후기를 작성했습니다.")

            # 후기 생성
            review = await self.crud.create_review(
                pod_id=request.pod_id,
                user_id=user_id,
                rating=request.rating,
                content=request.content,
            )

            if not review:
                logger.error(
                    f"후기 생성 실패: user_id={user_id}, pod_id={request.pod_id}"
                )
                return None

            logger.info(f"후기 생성 성공: review_id={review.id}")

            # 리뷰 생성 알림 전송
            await self._send_review_created_notification(
                review.id, request.pod_id, user_id
            )

            return await self._convert_to_dto(review)

        except Exception as e:
            logger.error(
                f"후기 생성 중 예외 발생: {type(e).__name__}: {str(e)}", exc_info=True
            )
            raise

    async def get_review_by_id(self, review_id: int) -> Optional[PodReviewDto]:
        """ID로 후기 조회"""
        review = await self.crud.get_review_by_id(review_id)
        if not review:
            return None

        return await self._convert_to_dto(review)

    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 파티의 후기 목록 조회"""
        reviews, total_count = await self.crud.get_reviews_by_pod(pod_id, page, size)

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodReviewDto](
            items=review_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 작성한 후기 목록 조회"""
        reviews, total_count = await self.crud.get_reviews_by_user(user_id, page, size)

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodReviewDto](
            items=review_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_reviews_received_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 참여한 파티에 대한 받은 리뷰 목록 조회 (본인이 작성한 리뷰 제외)"""
        reviews, total_count = await self.crud.get_reviews_received_by_user(
            user_id, page, size
        )

        review_dtos = []
        for review in reviews:
            review_dto = await self._convert_to_dto(review)
            review_dtos.append(review_dto)

        # PageDto 생성
        total_pages = math.ceil(total_count / size) if total_count > 0 else 0

        return PageDto[PodReviewDto](
            items=review_dtos,
            current_page=page,
            size=size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def update_review(
        self, review_id: int, user_id: int, request: PodReviewUpdateRequest
    ) -> Optional[PodReviewDto]:
        """후기 수정"""
        # 후기 존재 및 작성자 확인
        review = await self.crud.get_review_by_id(review_id)
        if not review:
            raise ValueError("후기를 찾을 수 없습니다.")

        if review.user_id != user_id:
            raise ValueError("본인이 작성한 후기만 수정할 수 있습니다.")

        # 후기 수정
        updated_review = await self.crud.update_review(
            review_id=review_id,
            rating=request.rating,
            content=request.content,
        )

        if not updated_review:
            return None

        return await self._convert_to_dto(updated_review)

    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """후기 삭제"""
        # 후기 존재 및 작성자 확인
        review = await self.crud.get_review_by_id(review_id)
        if not review:
            raise ValueError("후기를 찾을 수 없습니다.")

        if review.user_id != user_id:
            raise ValueError("본인이 작성한 후기만 삭제할 수 있습니다.")

        return await self.crud.delete_review(review_id)

    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회"""
        return await self.crud.get_review_stats_by_pod(pod_id)

    async def _convert_to_dto(self, review: PodReview) -> PodReviewDto:
        """PodReview 모델을 PodReviewDto로 변환"""
        try:
            logger.info(f"DTO 변환 시작: review_id={review.id}")

            # MissingGreenlet 오류 방지를 위해 수동으로 PodReviewDto 생성
            # review.pod와 review.user에 직접 접근하지 않고 필요한 정보만 사용

            # sub_categories 처리 (JSON 문자열을 리스트로 변환)
            # review.pod.sub_categories 대신 안전하게 처리
            sub_categories = []
            try:
                if hasattr(review, "pod") and review.pod:
                    sub_categories = review.pod.sub_categories or []
                    if isinstance(sub_categories, str):
                        import json

                        sub_categories = json.loads(sub_categories)
            except Exception as e:
                logger.warning(f"sub_categories 처리 중 오류 (무시): {e}")
                sub_categories = []

            logger.info(f"sub_categories 처리 완료: {sub_categories}")

            # SimplePodDto 생성 - 안전하게 처리
            try:
                simple_pod = SimplePodDto(
                    id=(
                        getattr(review.pod, "id", 0)
                        if hasattr(review, "pod") and review.pod
                        else 0
                    ),
                    owner_id=(
                        getattr(review.pod, "owner_id", 0)
                        if hasattr(review, "pod") and review.pod
                        else 0
                    ),
                    title=(
                        getattr(review.pod, "title", "")
                        if hasattr(review, "pod") and review.pod
                        else ""
                    ),
                    thumbnail_url=(
                        getattr(review.pod, "thumbnail_url", None)
                        or getattr(review.pod, "image_url", None)
                        if hasattr(review, "pod") and review.pod
                        else None
                    ),
                    sub_categories=sub_categories,
                    meeting_place=(
                        getattr(review.pod, "place", None)
                        if hasattr(review, "pod") and review.pod
                        else None
                    ),
                    meeting_date=_convert_to_combined_timestamp(
                        (
                            getattr(review.pod, "meeting_date", None)
                            if hasattr(review, "pod") and review.pod
                            else None
                        ),
                        (
                            getattr(review.pod, "meeting_time", None)
                            if hasattr(review, "pod") and review.pod
                            else None
                        ),
                    ),
                )
            except Exception as e:
                logger.error(f"SimplePodDto 생성 중 오류: {e}")
                # 기본값으로 SimplePodDto 생성
                simple_pod = SimplePodDto(
                    id=0,
                    owner_id=0,
                    title="",
                    thumbnail_url="",
                    sub_categories=[],
                    meeting_place="",
                    meeting_date=0,
                )

            logger.info(f"SimplePodDto 생성 완료: pod_id={simple_pod.id}")

            # SimpleUserDto 생성 - 안전하게 처리
            try:
                # 성향 타입 조회
                user_tendency_type = None
                if hasattr(review, "user") and review.user:
                    user_id = getattr(review.user, "id", 0)
                    if user_id:
                        from app.models.tendency import UserTendencyResult

                        result = await self.db.execute(
                            select(UserTendencyResult).where(
                                UserTendencyResult.user_id == user_id
                            )
                        )
                        user_tendency = result.scalar_one_or_none()
                        user_tendency_type = (
                            user_tendency.tendency_type if user_tendency else None
                        )

                user_follow = SimpleUserDto(
                    id=(
                        getattr(review.user, "id", 0)
                        if hasattr(review, "user") and review.user
                        else 0
                    ),
                    nickname=(
                        getattr(review.user, "nickname", "")
                        if hasattr(review, "user") and review.user
                        else ""
                    ),
                    profile_image=(
                        getattr(review.user, "profile_image", "") or ""
                        if hasattr(review, "user") and review.user
                        else ""
                    ),
                    intro=(
                        getattr(review.user, "intro", "") or ""
                        if hasattr(review, "user") and review.user
                        else ""
                    ),
                    tendency_type=user_tendency_type or "",
                    is_following=False,  # 필요시 별도 조회
                )
            except Exception as e:
                logger.error(f"SimpleUserDto 생성 중 오류: {e}")
                # 기본값으로 SimpleUserDto 생성
                user_follow = SimpleUserDto(
                    id=0,
                    nickname="",
                    profile_image="",
                    intro="",
                    tendency_type="",
                    is_following=False,
                )

            logger.info(f"SimpleUserDto 생성 완료: user_id={user_follow.id}")

            result = PodReviewDto(
                id=review.id,
                pod=simple_pod,
                user=user_follow,
                rating=review.rating,
                content=review.content,
                created_at=review.created_at,
                updated_at=review.updated_at,
            )

            logger.info(f"PodReviewDto 생성 완료: review_id={result.id}")
            return result

        except Exception as e:
            logger.error(
                f"PodReviewDto 생성 중 오류: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

    # - MARK: 리뷰 생성 알림 전송
    async def _send_review_created_notification(
        self, review_id: int, pod_id: int, reviewer_id: int
    ) -> None:
        """리뷰 생성 시 파티 참여자들에게 알림 전송"""
        try:
            # 리뷰 작성자 정보 조회
            reviewer_result = await self.db.execute(
                select(User).where(User.id == reviewer_id)
            )
            reviewer = reviewer_result.scalar_one_or_none()

            # 파티 정보 조회
            pod = await self.pod_crud.get_pod_by_id(pod_id)
            if not pod:
                logger.warning(f"파티 정보를 찾을 수 없음: pod_id={pod_id}")
                return

            if not reviewer:
                logger.warning(
                    f"리뷰 작성자 정보를 찾을 수 없음: reviewer_id={reviewer_id}"
                )
                return

            # 파티 참여자 목록 조회 (리뷰 작성자 제외)
            participants = await self.pod_crud.get_pod_participants(pod_id)

            if not participants:
                logger.info(f"파티 참여자가 없음: pod_id={pod_id}")
                return

            # FCM 서비스 초기화
            fcm_service = FCMService()

            # 각 참여자에게 알림 전송 (리뷰 작성자 제외)
            for participant in participants:
                if participant.id != reviewer_id:
                    try:
                        if participant.fcm_token:
                            await fcm_service.send_review_created(
                                token=participant.fcm_token,
                                nickname=reviewer.nickname,
                                party_name=pod.title,
                                review_id=review_id,
                                db=self.db,
                                user_id=participant.id,
                            )
                            logger.info(
                                f"리뷰 생성 알림 전송 성공: participant_id={participant.id}, review_id={review_id}"
                            )
                        else:
                            logger.warning(
                                f"FCM 토큰이 없는 참여자: participant_id={participant.id}"
                            )
                    except Exception as e:
                        logger.error(
                            f"리뷰 생성 알림 전송 실패: participant_id={participant.id}, error={e}"
                        )

        except Exception as e:
            logger.error(
                f"리뷰 생성 알림 처리 중 오류: review_id={review_id}, pod_id={pod_id}, error={e}"
            )
