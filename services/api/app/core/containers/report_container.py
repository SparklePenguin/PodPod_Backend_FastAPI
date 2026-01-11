"""Report Feature Containers"""

from dependency_injector import containers, providers


# MARK: - UseCase Containers
class ReportUseCaseContainer(containers.DeclarativeContainer):
    """신고 UseCase 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowRepoContainer
    from app.core.containers.user_container import (
        BlockUserRepoContainer,
        UserRepoContainer,
        UserReportRepoContainer,
    )
    from app.features.reports.use_cases.report_use_case import ReportUseCase

    core: CoreContainer = providers.DependenciesContainer()
    user_repo: UserRepoContainer = providers.DependenciesContainer()
    user_report_repo: UserReportRepoContainer = providers.DependenciesContainer()
    block_user_repo: BlockUserRepoContainer = providers.DependenciesContainer()
    follow_repo: FollowRepoContainer = providers.DependenciesContainer()

    report_use_case = providers.Factory(
        ReportUseCase,
        session=core.session,
        report_repo=user_report_repo.user_report_repo,
        user_repo=user_repo.user_repo,
        block_repo=block_user_repo.block_user_repo,
        follow_repo=follow_repo.follow_repo,
    )


# MARK: - Aggregate Container
class ReportContainer(containers.DeclarativeContainer):
    """신고 통합 컨테이너"""

    from app.core.containers.core_container import CoreContainer
    from app.core.containers.follow_container import FollowRepoContainer
    from app.core.containers.user_container import (
        BlockUserRepoContainer,
        UserRepoContainer,
        UserReportRepoContainer,
    )
    from app.features.reports.use_cases.report_use_case import ReportUseCase

    core: CoreContainer = providers.DependenciesContainer()

    # 필요한 컨테이너들 직접 생성
    user_repo: UserRepoContainer = providers.Container(UserRepoContainer, core=core)
    user_report_repo: UserReportRepoContainer = providers.Container(
        UserReportRepoContainer, core=core
    )
    block_user_repo: BlockUserRepoContainer = providers.Container(
        BlockUserRepoContainer, core=core
    )
    follow_repo: FollowRepoContainer = providers.Container(FollowRepoContainer, core=core)

    # UseCases
    use_case: ReportUseCaseContainer = providers.Container(
        ReportUseCaseContainer,
        core=core,
        user_repo=user_repo,
        user_report_repo=user_report_repo,
        block_user_repo=block_user_repo,
        follow_repo=follow_repo,
    )

    # 편의를 위한 alias
    report_use_case: providers.Factory[ReportUseCase] = use_case.report_use_case
