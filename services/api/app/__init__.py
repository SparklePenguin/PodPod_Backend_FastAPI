# 앱 버전 및 기본 설정
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가 (shared 모듈 import를 위해)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

__version__ = "1.0.0"
