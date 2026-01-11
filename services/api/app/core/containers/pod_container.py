"""Pod Feature Containers"""

from dependency_injector import containers, providers


# MARK: - Repository Containers
class PodRepoContainer(containers.DeclarativeContainer):
    """파티 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.repositories.pod_repository import PodRepository

    core: CoreContainer = providers.DependenciesContainer()

    pod_repo = providers.Factory(PodRepository, session=core.session)


class ApplicationRepoContainer(containers.DeclarativeContainer):
    """파티 신청 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.repositories.application_repository import (
        ApplicationRepository,
    )

    core: CoreContainer = providers.DependenciesContainer()

    application_repo = providers.Factory(ApplicationRepository, session=core.session)


class PodLikeRepoContainer(containers.DeclarativeContainer):
    """파티 좋아요 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.repositories.like_repository import PodLikeRepository

    core: CoreContainer = providers.DependenciesContainer()

    pod_like_repo = providers.Factory(PodLikeRepository, session=core.session)


class PodReviewRepoContainer(containers.DeclarativeContainer):
    """파티 리뷰 Repository 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.repositories.review_repository import PodReviewRepository

    core: CoreContainer = providers.DependenciesContainer()

    pod_review_repo = providers.Factory(PodReviewRepository, session=core.session)


class PodUserRepoContainer(containers.DeclarativeContainer):
    """파티용 사용자 Repository 컨테이너 (순환 참조 방지)"""

    from app.core.containers.core_container import CoreContainer
    from app.features.users.repositories import UserRepository

    core: CoreContainer = providers.DependenciesContainer()

    user_repo = providers.Factory(UserRepository, session=core.session)


# MARK: - Service Containers
class ReviewDtoServiceContainer(containers.DeclarativeContainer):
    """리뷰 DTO Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.services.review_dto_service import ReviewDtoService

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()

    review_dto_service = providers.Factory(
        ReviewDtoService,
        session=core.session,
        user_repo=user_repo.user_repo,
    )


class ApplicationDtoServiceContainer(containers.DeclarativeContainer):
    """신청 DTO Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.services.application_dto_service import ApplicationDtoService

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()

    application_dto_service = providers.Factory(
        ApplicationDtoService,
        session=core.session,
        user_repo=user_repo.user_repo,
    )


class LikeNotificationServiceContainer(containers.DeclarativeContainer):
    """좋아요 알림 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.services.like_notification_service import (
        LikeNotificationService,
    )

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    pod_like_repo: PodLikeRepoContainer = providers.DependenciesContainer()

    like_notification_service = providers.Factory(
        LikeNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        user_repo=user_repo.user_repo,
        pod_repo=pod_repo.pod_repo,
        like_repo=pod_like_repo.pod_like_repo,
    )


class ReviewNotificationServiceContainer(containers.DeclarativeContainer):
    """리뷰 알림 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.services.review_notification_service import (
        ReviewNotificationService,
    )

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()

    review_notification_service = providers.Factory(
        ReviewNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        user_repo=user_repo.user_repo,
        pod_repo=pod_repo.pod_repo,
    )


class ApplicationNotificationServiceContainer(containers.DeclarativeContainer):
    """신청 알림 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.services.application_notification_service import (
        ApplicationNotificationService,
    )

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    pod_like_repo: PodLikeRepoContainer = providers.DependenciesContainer()

    application_notification_service = providers.Factory(
        ApplicationNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        user_repo=user_repo.user_repo,
        pod_repo=pod_repo.pod_repo,
        like_repo=pod_like_repo.pod_like_repo,
    )


class PodNotificationServiceContainer(containers.DeclarativeContainer):
    """파티 알림 Service 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.services.pod_notification_service import (
        PodNotificationService,
    )

    core: CoreContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()

    pod_notification_service = providers.Factory(
        PodNotificationService,
        session=core.session,
        fcm_service=core.fcm_service,
        pod_repo=pod_repo.pod_repo,
    )


class PodEnrichmentServiceContainer(containers.DeclarativeContainer):
    """파티 enrichment Service 컨테이너"""

    from app.features.pods.services.pod_enrichment_service import PodEnrichmentService

    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    application_repo: ApplicationRepoContainer = providers.DependenciesContainer()
    pod_review_repo: PodReviewRepoContainer = providers.DependenciesContainer()
    pod_like_repo: PodLikeRepoContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    application_dto_service: ApplicationDtoServiceContainer = providers.DependenciesContainer()
    review_dto_service: ReviewDtoServiceContainer = providers.DependenciesContainer()

    pod_enrichment_service = providers.Factory(
        PodEnrichmentService,
        pod_repo=pod_repo.pod_repo,
        application_repo=application_repo.application_repo,
        review_repo=pod_review_repo.pod_review_repo,
        like_repo=pod_like_repo.pod_like_repo,
        user_repo=user_repo.user_repo,
        application_dto_service=application_dto_service.application_dto_service,
        review_dto_service=review_dto_service.review_dto_service,
    )


# MARK: - UseCase Containers
class ApplicationUseCaseContainer(containers.DeclarativeContainer):
    """신청 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.use_cases.application_use_case import ApplicationUseCase

    core: CoreContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    application_repo: ApplicationRepoContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    notification_service: ApplicationNotificationServiceContainer = (
        providers.DependenciesContainer()
    )

    application_use_case = providers.Factory(
        ApplicationUseCase,
        session=core.session,
        pod_repo=pod_repo.pod_repo,
        application_repo=application_repo.application_repo,
        user_repo=user_repo.user_repo,
        notification_service=notification_service.application_notification_service,
    )


class LikeUseCaseContainer(containers.DeclarativeContainer):
    """좋아요 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.use_cases.like_use_case import LikeUseCase

    core: CoreContainer = providers.DependenciesContainer()
    pod_like_repo: PodLikeRepoContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    notification_service: LikeNotificationServiceContainer = providers.DependenciesContainer()

    like_use_case = providers.Factory(
        LikeUseCase,
        session=core.session,
        like_repo=pod_like_repo.pod_like_repo,
        pod_repo=pod_repo.pod_repo,
        notification_service=notification_service.like_notification_service,
    )


class ReviewUseCaseContainer(containers.DeclarativeContainer):
    """리뷰 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.features.pods.use_cases.review_use_case import ReviewUseCase

    core: CoreContainer = providers.DependenciesContainer()
    pod_review_repo: PodReviewRepoContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    notification_service: ReviewNotificationServiceContainer = providers.DependenciesContainer()

    review_use_case = providers.Factory(
        ReviewUseCase,
        session=core.session,
        review_repo=pod_review_repo.pod_review_repo,
        pod_repo=pod_repo.pod_repo,
        user_repo=user_repo.user_repo,
        notification_service=notification_service.review_notification_service,
    )


class PodQueryUseCaseContainer(containers.DeclarativeContainer):
    """파티 조회 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowUseCaseContainer
    from app.features.pods.use_cases.pod_query_use_case import PodQueryUseCase

    core: CoreContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    user_repo: PodUserRepoContainer = providers.DependenciesContainer()
    enrichment_service: PodEnrichmentServiceContainer = providers.DependenciesContainer()
    follow_use_case: FollowUseCaseContainer = providers.DependenciesContainer()

    pod_query_use_case = providers.Factory(
        PodQueryUseCase,
        session=core.session,
        pod_repo=pod_repo.pod_repo,
        user_repo=user_repo.user_repo,
        enrichment_service=enrichment_service.pod_enrichment_service,
        follow_use_case=follow_use_case.follow_use_case,
    )


class PodUseCaseContainer(containers.DeclarativeContainer):
    """파티 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowUseCaseContainer
    from app.features.pods.use_cases.pod_use_case import PodUseCase

    core: CoreContainer = providers.DependenciesContainer()
    pod_repo: PodRepoContainer = providers.DependenciesContainer()
    enrichment_service: PodEnrichmentServiceContainer = providers.DependenciesContainer()
    notification_service: PodNotificationServiceContainer = providers.DependenciesContainer()
    follow_use_case: FollowUseCaseContainer = providers.DependenciesContainer()

    pod_use_case = providers.Factory(
        PodUseCase,
        session=core.session,
        pod_repo=pod_repo.pod_repo,
        enrichment_service=enrichment_service.pod_enrichment_service,
        notification_service=notification_service.pod_notification_service,
        follow_use_case=follow_use_case.follow_use_case,
    )


# MARK: - Aggregate Container
class PodContainer(containers.DeclarativeContainer):
    """파티 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowUseCaseContainer

    core: CoreContainer = providers.DependenciesContainer()

    # FollowUseCaseContainer를 직접 생성
    follow_use_case: FollowUseCaseContainer = providers.Container(
        FollowUseCaseContainer, core=core
    )

    # Repositories
    pod_repo: PodRepoContainer = providers.Container(PodRepoContainer, core=core)
    application_repo: ApplicationRepoContainer = providers.Container(
        ApplicationRepoContainer, core=core
    )
    pod_like_repo: PodLikeRepoContainer = providers.Container(
        PodLikeRepoContainer, core=core
    )
    pod_review_repo: PodReviewRepoContainer = providers.Container(
        PodReviewRepoContainer, core=core
    )
    user_repo: PodUserRepoContainer = providers.Container(PodUserRepoContainer, core=core)

    # Services
    review_dto_service: ReviewDtoServiceContainer = providers.Container(
        ReviewDtoServiceContainer, core=core, user_repo=user_repo
    )
    application_dto_service: ApplicationDtoServiceContainer = providers.Container(
        ApplicationDtoServiceContainer, core=core, user_repo=user_repo
    )
    like_notification_service: LikeNotificationServiceContainer = providers.Container(
        LikeNotificationServiceContainer,
        core=core,
        user_repo=user_repo,
        pod_repo=pod_repo,
        pod_like_repo=pod_like_repo,
    )
    review_notification_service: ReviewNotificationServiceContainer = providers.Container(
        ReviewNotificationServiceContainer,
        core=core,
        user_repo=user_repo,
        pod_repo=pod_repo,
    )
    application_notification_service: ApplicationNotificationServiceContainer = (
        providers.Container(
            ApplicationNotificationServiceContainer,
            core=core,
            user_repo=user_repo,
            pod_repo=pod_repo,
            pod_like_repo=pod_like_repo,
        )
    )
    pod_notification_service: PodNotificationServiceContainer = providers.Container(
        PodNotificationServiceContainer,
        core=core,
        pod_repo=pod_repo,
    )
    pod_enrichment_service: PodEnrichmentServiceContainer = providers.Container(
        PodEnrichmentServiceContainer,
        pod_repo=pod_repo,
        application_repo=application_repo,
        pod_review_repo=pod_review_repo,
        pod_like_repo=pod_like_repo,
        user_repo=user_repo,
        application_dto_service=application_dto_service,
        review_dto_service=review_dto_service,
    )

    # UseCases
    application_use_case: ApplicationUseCaseContainer = providers.Container(
        ApplicationUseCaseContainer,
        core=core,
        pod_repo=pod_repo,
        application_repo=application_repo,
        user_repo=user_repo,
        notification_service=application_notification_service,
    )
    like_use_case: LikeUseCaseContainer = providers.Container(
        LikeUseCaseContainer,
        core=core,
        pod_like_repo=pod_like_repo,
        pod_repo=pod_repo,
        notification_service=like_notification_service,
    )
    review_use_case: ReviewUseCaseContainer = providers.Container(
        ReviewUseCaseContainer,
        core=core,
        pod_review_repo=pod_review_repo,
        pod_repo=pod_repo,
        user_repo=user_repo,
        notification_service=review_notification_service,
    )
    pod_query_use_case: PodQueryUseCaseContainer = providers.Container(
        PodQueryUseCaseContainer,
        core=core,
        pod_repo=pod_repo,
        user_repo=user_repo,
        enrichment_service=pod_enrichment_service,
        follow_use_case=follow_use_case,
    )
    pod_use_case: PodUseCaseContainer = providers.Container(
        PodUseCaseContainer,
        core=core,
        pod_repo=pod_repo,
        enrichment_service=pod_enrichment_service,
        notification_service=pod_notification_service,
        follow_use_case=follow_use_case,
    )
