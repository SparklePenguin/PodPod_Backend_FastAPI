#!/bin/bash

# PodPod Backend - 시스템 의존성 설치 스크립트
# 이 스크립트는 최초 1회만 실행하면 됩니다.
# 완료 후 scripts/.setup 파일이 생성됩니다.

set -e  # 오류 발생시 즉시 중단

echo "🔧 PodPod Backend - 시스템 의존성 설치"
echo "=========================================="
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.." || exit 1
PROJECT_ROOT=$(pwd)

echo "📁 프로젝트 경로: $PROJECT_ROOT"
echo ""

# OS 감지
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
fi

echo "💻 운영체제: $OS_TYPE"
echo ""

# Homebrew 설치 확인 (macOS only)
if [ "$OS_TYPE" = "macos" ]; then
    echo "🍺 Checking Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew가 설치되지 않았습니다."
        echo "📝 Homebrew 설치 방법:"
        echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        echo ""
        exit 1
    else
        echo "✅ Homebrew가 설치되어 있습니다."
    fi
    echo ""
fi

# 1. pyenv 설치 확인
echo "🐍 Checking pyenv..."
if ! command -v pyenv &> /dev/null; then
    echo "⚠️  pyenv가 설치되지 않았습니다."
    echo ""
    read -p "pyenv를 설치하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$OS_TYPE" = "macos" ]; then
            brew install pyenv
        elif [ "$OS_TYPE" = "linux" ]; then
            curl https://pyenv.run | bash
        fi

        echo ""
        echo "✅ pyenv 설치 완료"
        echo "📝 다음 설정을 shell 설정 파일에 추가하세요:"
        echo ""
        echo '  # For bash (~/.bashrc or ~/.bash_profile)'
        echo '  export PYENV_ROOT="$HOME/.pyenv"'
        echo '  command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
        echo '  eval "$(pyenv init -)"'
        echo ""
        echo '  # For zsh (~/.zshrc)'
        echo '  export PYENV_ROOT="$HOME/.pyenv"'
        echo '  command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
        echo '  eval "$(pyenv init -)"'
        echo ""
        echo "⚠️  설정 후 터미널을 재시작하고 다시 이 스크립트를 실행하세요."
        exit 0
    else
        echo "❌ pyenv 설치가 취소되었습니다."
        exit 1
    fi
else
    echo "✅ pyenv가 설치되어 있습니다."
fi
echo ""

# pyenv 초기화
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)" 2>/dev/null || true

# Python 버전 확인 및 설치
echo "🐍 Checking Python version..."
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
else
    PYTHON_VERSION="3.9.20"
    echo "$PYTHON_VERSION" > .python-version
fi

if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
    echo "⚠️  Python ${PYTHON_VERSION}이(가) 설치되지 않았습니다."
    echo ""
    read -p "Python ${PYTHON_VERSION}을(를) 설치하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pyenv install ${PYTHON_VERSION}
        pyenv local ${PYTHON_VERSION}
        echo "✅ Python ${PYTHON_VERSION} 설치 완료"
    else
        echo "❌ Python 설치가 취소되었습니다."
        exit 1
    fi
else
    echo "✅ Python ${PYTHON_VERSION}이(가) 설치되어 있습니다."
    pyenv local ${PYTHON_VERSION}
fi
echo ""

# 2. uv 설치 확인
echo "🚀 Checking uv (fast Python package installer)..."
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv가 설치되지 않았습니다."
    echo ""
    read -p "uv를 설치하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$OS_TYPE" = "macos" ]; then
            brew install uv
        elif [ "$OS_TYPE" = "linux" ]; then
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
        echo "✅ uv 설치 완료"
    else
        echo "⚠️  uv 설치를 건너뜁니다. (pip를 사용합니다)"
    fi
else
    echo "✅ uv가 설치되어 있습니다."
fi
echo ""

# 3. Infisical CLI 설치 확인
echo "🔐 Checking Infisical CLI..."
if ! command -v infisical &> /dev/null; then
    echo "⚠️  Infisical CLI가 설치되지 않았습니다."
    echo ""
    read -p "Infisical CLI를 설치하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$OS_TYPE" = "macos" ]; then
            brew install infisical/infisical-cli/infisical
        elif [ "$OS_TYPE" = "linux" ]; then
            curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash
            sudo apt-get update && sudo apt-get install -y infisical
        fi
        echo "✅ Infisical CLI 설치 완료"
    else
        echo "❌ Infisical CLI 설치가 취소되었습니다."
        exit 1
    fi
else
    echo "✅ Infisical CLI가 설치되어 있습니다."
fi

# Infisical 로그인 확인
echo "🔐 Checking Infisical authentication..."
if ! infisical run --env=dev -- echo "check" </dev/null &> /dev/null; then
    echo "⚠️  Infisical에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  infisical login"
    echo ""
    read -p "지금 로그인하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        infisical login
    else
        echo "⚠️  나중에 'infisical login' 명령으로 로그인해주세요."
    fi
else
    echo "✅ Infisical 인증 완료"
fi
echo ""

# 4. MySQL 설치 확인
echo "🗄️  Checking MySQL..."
if ! command -v mysql &> /dev/null; then
    echo "⚠️  MySQL이 설치되지 않았습니다."
    echo ""
    read -p "MySQL을 설치하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$OS_TYPE" = "macos" ]; then
            brew install mysql
            echo ""
            echo "✅ MySQL 설치 완료"
            echo "📝 MySQL 서비스 시작:"
            echo "  brew services start mysql"
            echo ""
            read -p "지금 MySQL을 시작하시겠습니까? (y/n): " -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                brew services start mysql
                sleep 3
            fi
        elif [ "$OS_TYPE" = "linux" ]; then
            sudo apt-get update
            sudo apt-get install -y mysql-server
            echo ""
            echo "✅ MySQL 설치 완료"
            echo "📝 MySQL 서비스 시작:"
            echo "  sudo systemctl start mysql"
            echo ""
            read -p "지금 MySQL을 시작하시겠습니까? (y/n): " -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo systemctl start mysql
                sudo systemctl enable mysql
                sleep 3
            fi
        fi
    else
        echo "⚠️  MySQL 설치를 건너뜁니다. (Docker 환경에서는 필수 아님)"
    fi
else
    echo "✅ MySQL이 설치되어 있습니다."
fi
echo ""

# 5. Docker 설치 확인 (개발 환경용)
echo "🐳 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker가 설치되지 않았습니다."
    echo "📝 Docker 설치 방법:"
    if [ "$OS_TYPE" = "macos" ]; then
        echo "  - Docker Desktop for Mac: https://docs.docker.com/desktop/install/mac-install/"
    elif [ "$OS_TYPE" = "linux" ]; then
        echo "  - Docker Engine for Linux: https://docs.docker.com/engine/install/"
    fi
    echo ""
    echo "⚠️  Docker를 수동으로 설치한 후 다시 이 스크립트를 실행하세요."
    echo "    (로컬 환경만 사용하는 경우 Docker는 선택사항입니다)"
else
    echo "✅ Docker가 설치되어 있습니다."

    # Docker 실행 확인
    if docker info &> /dev/null; then
        echo "✅ Docker가 실행 중입니다."
    else
        echo "⚠️  Docker가 실행되지 않았습니다."
        echo "📝 Docker를 시작해주세요:"
        if [ "$OS_TYPE" = "macos" ]; then
            echo "  open -a Docker"
        elif [ "$OS_TYPE" = "linux" ]; then
            echo "  sudo systemctl start docker"
        fi
    fi
fi
echo ""

# .env 파일 확인
echo "🔑 Checking .env file..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo ""
    if [ -f ".env.example" ]; then
        read -p ".env.example을 복사하여 .env 파일을 생성하시겠습니까? (y/n): " -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            echo "✅ .env 파일이 생성되었습니다."
            echo "📝 .env 파일을 열어서 필요한 환경 변수를 설정하세요."
        else
            echo "⚠️  나중에 .env 파일을 생성해주세요: cp .env.example .env"
        fi
    else
        echo "⚠️  .env.example 파일도 없습니다. 수동으로 .env 파일을 생성해주세요."
    fi
else
    echo "✅ .env 파일이 존재합니다."
fi
echo ""

# 설치 완료 마커 파일 생성
echo "=========================================="
echo "✅ 시스템 의존성 설치 완료!"
echo "=========================================="
echo ""

# .setup 파일 생성 (설치 완료 표시)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cat > "$SCRIPT_DIR/.setup" <<EOF
# PodPod Backend - 시스템 의존성 설치 완료
# 생성일시: $(date)
#
# 이 파일은 시스템 의존성이 설치되었음을 표시합니다.
# 재설치가 필요한 경우 이 파일을 삭제하고 setup-dependencies.sh를 다시 실행하세요.

SETUP_DATE=$(date +%s)
SETUP_OS=$OS_TYPE
SETUP_PYTHON_VERSION=$PYTHON_VERSION
EOF

echo "📄 scripts/.setup 파일 생성 완료"
echo ""
echo "📝 다음 단계:"
echo "  1. Python 패키지 설치: bash scripts/install-packages.sh"
echo "  2. 로컬 환경 실행: bash scripts/start-local.sh"
echo "  또는"
echo "  2. 개발 환경 실행: bash scripts/start-dev.sh"
echo ""
