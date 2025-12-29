import math
from datetime import datetime, time, timezone

from app.common.schemas import PageDto
from app.core.logging_config import get_logger
from app.core.services.fcm_service import FCMService
from app.features.users.schemas import UserDto
from app.features.pods.models.pod_review import PodReview
from app.features.pods.repositories.pod_repository import PodRepository
from app.features.pods.repositories.review_repository import PodReviewRepository
from app.features.pods.schemas import (
    PodReviewCreateRequest,
    PodReviewDto,
    PodReviewUpdateRequest,
    PodDto,
)
from app.features.users.models import User
from app.features.users.repositories import UserRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("pod_review_service")


def _convert_to_combined_timestamp(meeting_date, meeting_time):
    """date와 time 객체를 UTC로 해석하여 하나의 timestamp로 변환"""
    if meeting_date is None:
        return None
    if meeting_time is None:
        # time이 없으면 date만 사용 (00:00:00)
        dt = datetime.combine(meeting_date, time.min, tzinfo=timezone.utc)
    else:
        # date와 time을 결합 (UTC로 해석)
        dt = datetime.combine(meeting_date, meeting_time, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)  # milliseconds


class PodReviewService:
    def __init__(self, session: AsyncSession, fcm_service: FCMService | None = None):
        self._session = session
        self.pod_review_repo = PodReviewRepository(session)
        self.pod_repo = PodRepository(session)
        self.user_repo = UserRepository(session)
        self._fcm_service = fcm_service or FCMService()

    # - MARK: 후기 생성
    async def create_review(
        self, user_id: int, request: PodReviewCreateRequest
    ) -> PodReviewDto | None:
        """후기 생성"""
        try:
            # 이미 작성한 후기가 있는지 확인
            existing_review = await self.pod_review_repo.get_review_by_pod_and_user(
                request.pod_id, user_id
            )
            if existing_review:
                from app.features.pods.exceptions import ReviewAlreadyExistsException

                raise ReviewAlreadyExistsException(request.pod_id, user_id)

            # 후기 생성
            review = await self.pod_review_repo.create_review(
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

            if review.id is None:
                raise ValueError("후기 생성 후 ID를 가져올 수 없습니다.")

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

    # - MARK: ID로 후기 조회
    async def get_review_by_id(self, review_id: int) -> PodReviewDto:
        """ID로 후기 조회"""
        review = await self.pod_review_repo.get_review_by_id(review_id)
        if not review:
            from app.features.pods.exceptions import ReviewNotFoundException

            raise ReviewNotFoundException(review_id)

        return await self._convert_to_dto(review)

    # - MARK: 특정 파티의 후기 목록 조회
    async def get_reviews_by_pod(
        self, pod_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 파티의 후기 목록 조회"""
        reviews, total_count = await self.pod_review_repo.get_reviews_by_pod(
            pod_id, page, size
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

    async def get_reviews_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 작성한 후기 목록 조회"""
        reviews, total_count = await self.pod_review_repo.get_reviews_by_user(
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

    async def get_reviews_received_by_user(
        self, user_id: int, page: int = 1, size: int = 20
    ) -> PageDto[PodReviewDto]:
        """특정 사용자가 참여한 파티에 대한 받은 리뷰 목록 조회 (본인이 작성한 리뷰 제외)"""
        reviews, total_count = await self.pod_review_repo.get_reviews_received_by_user(
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

    # - MARK: 후기 수정
    async def update_review(
        self, review_id: int, user_id: int, request: PodReviewUpdateRequest
    ) -> PodReviewDto | None:
        """후기 수정"""
        # 후기 존재 및 작성자 확인
        review = await self.pod_review_repo.get_review_by_id(review_id)
        if not review:
            from app.features.pods.exceptions import ReviewNotFoundException

            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            from app.features.pods.exceptions import ReviewPermissionDeniedException

            raise ReviewPermissionDeniedException(review_id, user_id)

        # 후기 수정
        updated_review = await self.pod_review_repo.update_review(
            review_id=review_id, rating=request.rating, content=request.content
        )

        if not updated_review:
            from app.features.pods.exceptions import ReviewNotFoundException

            raise ReviewNotFoundException(review_id)

        return await self._convert_to_dto(updated_review)

    # - MARK: 후기 삭제
    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """후기 삭제"""
        # 후기 존재 및 작성자 확인
        review = await self.pod_review_repo.get_review_by_id(review_id)
        if not review:
            from app.features.pods.exceptions import ReviewNotFoundException

            raise ReviewNotFoundException(review_id)

        if review.user_id != user_id:
            from app.features.pods.exceptions import ReviewPermissionDeniedException

            raise ReviewPermissionDeniedException(review_id, user_id)

        return await self.pod_review_repo.delete_review(review_id)

    # - MARK: 파티별 후기 통계 조회
    async def get_review_stats_by_pod(self, pod_id: int) -> dict:
        """파티별 후기 통계 조회"""
        return await self.pod_review_repo.get_review_stats_by_pod(pod_id)

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

            # PodDto 생성 - 안전하게 처리
            try:
                pod = review.pod if hasattr(review, "pod") and review.pod else None
                simple_pod = PodDto(
                    id=pod.id or 0 if pod else 0,
                    owner_id=pod.owner_id or 0 if pod else 0,
                    title=pod.title or "" if pod else "",
                    thumbnail_url=(pod.thumbnail_url or pod.image_url or "")
                    if pod
                    else "",
                    sub_categories=sub_categories,
                    meeting_place=pod.place or "" if pod else "",
                    meeting_date=_convert_to_combined_timestamp(
                        pod.meeting_date if pod else None,
                        pod.meeting_time if pod else None,
                    )
                    or 0,
                )
            except Exception as e:
                logger.error(f"PodDto 생성 중 오류: {e}")
                # 기본값으로 PodDto 생성
                simple_pod = PodDto(
                    id=0,
                    owner_id=0,
                    title="",
                    thumbnail_url="",
                    sub_categories=[],
                    meeting_place="",
                    meeting_date=0,
                )

            logger.info(f"PodDto 생성 완료: pod_id={simple_pod.id}")

            # UserDto 생성 - 안전하게 처리
            try:
                # 성향 타입 조회
                user_tendency_type = None
                user = review.user if hasattr(review, "user") and review.user else None
                if user and user.id:
                    from app.features.tendencies.models import UserTendencyResult

                    result = await self._session.execute(
                        select(UserTendencyResult).where(
                            UserTendencyResult.user_id == user.id
                        )
                    )
                    user_tendency = result.scalar_one_or_none()
                    user_tendency_type = (
                        user_tendency.tendency_type or "" if user_tendency else ""
                    )

                user_follow = UserDto(
                    id=user.id or 0 if user else 0,
                    nickname=user.nickname or "" if user else "",
                    profile_image=user.profile_image or "" if user else "",
                    intro=user.intro or "" if user else "",
                    tendency_type=user_tendency_type or "",
                    is_following=False,  # 필요시 별도 조회
                )
            except Exception as e:
                logger.error(f"UserDto 생성 중 오류: {e}")
                # 기본값으로 UserDto 생성
                user_follow = UserDto(
                    id=0,
                    nickname="",
                    profile_image="",
                    intro="",
                    tendency_type="",
                    is_following=False,
                )

            logger.info(f"UserDto 생성 완료: user_id={user_follow.id}")

            if review.id is None or review.rating is None:
                raise ValueError("후기 정보가 올바르지 않습니다.")

            review_created_at = review.created_at
            if review_created_at is None:
                from datetime import datetime, timezone

                review_created_at = datetime.now(timezone.utc).replace(tzinfo=None)

            review_updated_at = review.updated_at
            if review_updated_at is None:
                from datetime import datetime, timezone

                review_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

            result = PodReviewDto(
                id=review.id,
                pod=simple_pod,
                user=user_follow,
                rating=review.rating,
                content=review.content or "",
                created_at=review_created_at,
                updated_at=review_updated_at,
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
            reviewer_result = await self._session.execute(
                select(User).where(User.id == reviewer_id)
            )
            reviewer = reviewer_result.scalar_one_or_none()

            # 파티 정보 조회
            pod = await self.pod_repo.get_pod_by_id(pod_id)
            if not pod:
                logger.warning(f"파티 정보를 찾을 수 없음: pod_id={pod_id}")
                return

            if not reviewer:
                logger.warning(
                    f"리뷰 작성자 정보를 찾을 수 없음: reviewer_id={reviewer_id}"
                )
                return

            # 파티장 정보 조회
            owner_result = await self._session.execute(
                select(User).where(User.id == pod.owner_id)
            )
            owner = owner_result.scalar_one_or_none()

            if not owner:
                logger.warning(f"파티장 정보를 찾을 수 없음: pod_id={pod_id}")
                return

            # FCM 서비스 초기화

            # 파티장에게만 알림 전송 (리뷰 작성자가 파티장이 아닌 경우)
            if owner.id is not None and owner.id != reviewer_id:
                try:
                    if owner.fcm_token:
                        await self._fcm_service.send_review_created(
                            token=owner.fcm_token,
                            nickname=reviewer.nickname or "",
                            party_name=pod.title or "",
                            review_id=review_id,
                            db=self._session,
                            user_id=owner.id,
                            related_user_id=reviewer_id,  # 리뷰 작성자
                            related_pod_id=pod_id,  # 리뷰를 남긴 파티
                        )
                        logger.info(
                            f"리뷰 생성 알림 전송 성공 (파티장): owner_id={owner.id}, review_id={review_id}"
                        )
                    else:
                        logger.warning(f"파티장 FCM 토큰이 없음: owner_id={owner.id}")
                except Exception as e:
                    logger.error(
                        f"리뷰 생성 알림 전송 실패 (파티장): owner_id={owner.id}, error={e}"
                    )

            # 리뷰 작성자 제외 참여자들에게 REVIEW_OTHERS_CREATED 알림 전송
            participants = await self.pod_repo.get_pod_participants(pod_id)
            reviewer_nickname = reviewer.nickname or ""
            for participant in participants:
                # 리뷰 작성자 제외
                if participant.id is not None and participant.id == reviewer_id:
                    continue
                # 파티장은 이미 REVIEW_CREATED를 받았으므로 제외
                if (
                    participant.id is not None
                    and pod.owner_id is not None
                    and participant.id == pod.owner_id
                ):
                    continue

                try:
                    if participant.fcm_token:
                        await self._fcm_service.send_review_others_created(
                            token=participant.fcm_token,
                            nickname=reviewer_nickname,
                            review_id=review_id,
                            pod_id=pod_id,
                            db=self._session,
                            user_id=participant.id,
                            related_user_id=reviewer_id,
                        )
                        logger.info(
                            f"다른 사람 리뷰 생성 알림 전송 성공: participant_id={participant.id}, review_id={review_id}"
                        )
                    else:
                        logger.warning(
                            f"FCM 토큰이 없는 참여자: participant_id={participant.id}"
                        )
                except Exception as e:
                    logger.error(
                        f"다른 사람 리뷰 생성 알림 전송 실패: participant_id={participant.id}, error={e}"
                    )

        except Exception as e:
            logger.error(
                f"리뷰 생성 알림 처리 중 오류: review_id={review_id}, pod_id={pod_id}, error={e}"
            )
