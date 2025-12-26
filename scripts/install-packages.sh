#!/bin/bash

# PodPod Backend - Python 패키지 설치 스크립트
# 이 스크립트는 패키지 업데이트가 필요할 때마다 실행할 수 있습니다.
# 완료 후 .venv/.packages_installed 파일이 생성됩니다.

set -e  # 오류 발생시 즉시 중단

echo "📦 PodPod Backend - Python 패키지 설치"
echo "=========================================="
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.." || exit 1
PROJECT_ROOT=$(pwd)

echo "📁 프로젝트 경로: $PROJECT_ROOT"
echo ""

# .setup 파일 확인
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$SCRIPT_DIR/.setup" ]; then
    echo "⚠️  시스템 의존성이 설치되지 않았습니다."
    echo "📝 먼저 다음 명령을 실행하세요:"
    echo "  bash scripts/setup-dependencies.sh"
    echo ""
    exit 1
fi

echo "✅ 시스템 의존성 확인 완료"
echo ""

# pyenv 초기화
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)" 2>/dev/null || true

# Python 버전 확인
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
    echo "📌 Python 버전: $PYTHON_VERSION"
else
    echo "❌ .python-version 파일이 없습니다."
    exit 1
fi

# Python 경로 설정
PYTHON_BIN="$(pyenv which python)"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "⚠️  Python을 찾을 수 없습니다."
    echo "📝 다음 명령으로 Python을 설치하세요:"
    echo "  pyenv install $PYTHON_VERSION"
    exit 1
fi

echo "🐍 Python: $($PYTHON_BIN --version)"
echo "📍 경로: $PYTHON_BIN"
echo ""

# 강제 재설치 옵션
FORCE_REINSTALL=false
if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    FORCE_REINSTALL=true
    echo "🔄 강제 재설치 모드"
    echo ""
fi

# 패키지 관리자 결정 (uv 우선, 없으면 pip)
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    echo "🚀 패키지 관리자: uv (fast Python package installer)"
else
    echo "📦 패키지 관리자: pip (uv가 없습니다)"
    echo "💡 더 빠른 설치를 원하시면 uv를 설치하세요: brew install uv"
fi
echo ""

# 가상환경 확인 및 생성
if [ ! -d ".venv" ]; then
    echo "📦 가상환경 생성 중..."
    if [ "$USE_UV" = true ]; then
        uv venv .venv --python "$PYTHON_BIN"
    else
        $PYTHON_BIN -m venv .venv
    fi

    if [ $? -eq 0 ]; then
        echo "✅ 가상환경 생성 완료"
    else
        echo "❌ 가상환경 생성 실패"
        exit 1
    fi
else
    echo "✅ 가상환경이 이미 존재합니다."

    if [ "$FORCE_REINSTALL" = true ]; then
        echo "🗑️  기존 패키지 설치 마커 삭제..."
        rm -f .venv/.installed
    fi
fi

echo ""

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ 가상환경 활성화 실패"
    exit 1
fi

echo "✅ 가상환경 활성화 완료"
echo ""

# 패키지 설치
if [ ! -f ".venv/.installed" ] || [ "$FORCE_REINSTALL" = true ]; then
    echo "=========================================="
    echo "📥 패키지 설치 시작"
    echo "=========================================="
    echo ""

    if [ "$USE_UV" = true ]; then
        # uv를 사용한 설치
        echo "🚀 uv를 사용하여 패키지 설치 중..."
        echo ""

        # pyproject.toml이 있으면 사용, 없으면 requirements.txt 사용
        if [ -f "pyproject.toml" ]; then
            echo "📄 pyproject.toml 기반 설치"
            uv pip install -e .
        elif [ -f "requirements.txt" ]; then
            echo "📄 requirements.txt 기반 설치"
            uv pip install -r requirements.txt
        else
            echo "❌ pyproject.toml 또는 requirements.txt 파일이 없습니다."
            exit 1
        fi

        # 개발 의존성 설치 (선택사항)
        if [ -f "pyproject.toml" ] && grep -q '\[project.optional-dependencies\]' pyproject.toml; then
            echo ""
            read -p "개발 의존성도 설치하시겠습니까? (y/n): " -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                uv pip install -e ".[dev]"
                echo "✅ 개발 의존성 설치 완료"
            fi
        fi
    else
        # pip를 사용한 설치
        echo "⬆️  pip 업그레이드..."
        pip install --upgrade pip
        echo ""

        # pyproject.toml이 있으면 사용, 없으면 requirements.txt 사용
        if [ -f "pyproject.toml" ]; then
            echo "📄 pyproject.toml 기반 설치"
            pip install -e .
        elif [ -f "requirements.txt" ]; then
            echo "📄 requirements.txt 기반 설치"
            pip install -r requirements.txt
        else
            echo "❌ pyproject.toml 또는 requirements.txt 파일이 없습니다."
            exit 1
        fi

        # 개발 의존성 설치 (선택사항)
        if [ -f "pyproject.toml" ] && grep -q '\[project.optional-dependencies\]' pyproject.toml; then
            echo ""
            read -p "개발 의존성도 설치하시겠습니까? (y/n): " -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pip install -e ".[dev]"
                echo "✅ 개발 의존성 설치 완료"
            fi
        fi
    fi

    echo ""
    echo "=========================================="
    echo "✅ 패키지 설치 완료!"
    echo "=========================================="
    echo ""

    # 설치 완료 마커 파일 생성
    cat > ".venv/.installed" <<EOF
# PodPod Backend - Python 패키지 설치 완료
# 생성일시: $(date)
#
# 이 파일은 Python 패키지가 설치되었음을 표시합니다.
# 재설치가 필요한 경우:
#   1. 이 파일을 삭제: rm .venv/.installed
#   2. 재설치 실행: bash scripts/install-packages.sh
# 또는
#   강제 재설치: bash scripts/install-packages.sh --force

INSTALL_DATE=$(date +%s)
PYTHON_VERSION=$($PYTHON_BIN --version)
PACKAGE_MANAGER=$(if [ "$USE_UV" = true ]; then echo "uv"; else echo "pip"; fi)
EOF

    echo "📄 .venv/.installed 파일 생성 완료"

else
    echo "✅ 패키지가 이미 설치되어 있습니다."
    echo "💡 재설치하려면 다음 중 하나를 실행하세요:"
    echo "  - rm .venv/.installed && bash scripts/install-packages.sh"
    echo "  - bash scripts/install-packages.sh --force"
fi

echo ""
echo "📝 다음 단계:"
echo "  - 로컬 환경 실행: bash scripts/start-local.sh"
echo "  - 개발 환경 실행: bash scripts/start-dev.sh"
echo ""
