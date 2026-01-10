"""의존성 주입 컨테이너 (호환성 유지용)

실제 구현은 app.core.containers 패키지로 분리되었습니다.
이 파일은 기존 import를 유지하기 위한 re-export입니다.
"""

from app.core.containers import ApplicationContainer, container

# 기존 코드와의 호환성을 위해 Container alias 제공
Container = ApplicationContainer

__all__ = ["Container", "ApplicationContainer", "container"]
