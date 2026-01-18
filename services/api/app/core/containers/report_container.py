"""Report Feature Containers

신고 관련 컨테이너들.
실제 조립은 ReportFeatureContainer(application_container.py)에서 수행됨.
"""

from dependency_injector import containers, providers

from app.core.containers.core_container import CoreContainer
from app.core.containers.follow_container import FollowRepoContainer
from app.core.containers.user_container import (
    BlockUserRepoContainer,
    UserRepoContainer,
    UserReportRepoContainer,
)
from app.features.reports.use_cases.report_use_case import ReportUseCase


# MARK: - UseCase Containers
class ReportUseCaseContainer(containers.DeclarativeContainer):
    """신고 UseCase 컨테이너
    
    의존성:
    - core: DB 세션
    - user_repo: 사용자 조회 (user_feature에서 주입)
    - user_report_repo: 신고 저장
    - block_user_repo: 차단 처리
    - follow_repo: 팔로우 해제
    """

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