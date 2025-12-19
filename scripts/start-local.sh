#!/bin/bash

# PodPod Backend - 로컬 가상환경 실행 스크립트

echo "🚀 Starting PodPod Backend (Local Environment with Virtual Environment)..."
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.." || exit 1
PROJECT_ROOT=$(pwd)

echo "📁 프로젝트 경로: $PROJECT_ROOT"
echo ""

# pyenv 설치 확인
echo "🔍 Checking pyenv..."
if ! command -v pyenv &> /dev/null; then
    echo "⚠️  pyenv가 설치되지 않았습니다."
    echo ""

    # Homebrew 확인
    if command -v brew &> /dev/null; then
        read -p "pyenv를 자동으로 설치하시겠습니까? (y/n): " -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📥 pyenv 설치 중..."
            brew install pyenv

            if [ $? -eq 0 ]; then
                echo "✅ pyenv 설치 완료"
                echo ""
                echo "📝 Shell 설정에 pyenv를 추가해야 합니다."
                echo "   다음 명령어를 실행하세요:"
                echo ""
                echo "   echo 'export PYENV_ROOT=\"\$HOME/.pyenv\"' >> ~/.zshrc"
                echo "   echo 'command -v pyenv >/dev/null || export PATH=\"\$PYENV_ROOT/bin:\$PATH\"' >> ~/.zshrc"
                echo "   echo 'eval \"\$(pyenv init -)\"' >> ~/.zshrc"
                echo "   source ~/.zshrc"
                echo ""
                echo "   Shell 설정 후 이 스크립트를 다시 실행하세요."
                exit 0
            else
                echo "❌ pyenv 설치 실패"
                exit 1
            fi
        else
            echo "📝 pyenv 수동 설치 방법:"
            echo "  brew install pyenv"
            echo ""
            echo "  그 다음 shell 설정에 다음을 추가하세요:"
            echo "  echo 'export PYENV_ROOT=\"\$HOME/.pyenv\"' >> ~/.zshrc"
            echo "  echo 'command -v pyenv >/dev/null || export PATH=\"\$PYENV_ROOT/bin:\$PATH\"' >> ~/.zshrc"
            echo "  echo 'eval \"\$(pyenv init -)\"' >> ~/.zshrc"
            exit 1
        fi
    else
        echo "📝 Homebrew가 설치되어 있지 않습니다."
        echo "   pyenv 설치 방법:"
        echo "   1. Homebrew 설치: https://brew.sh"
        echo "   2. brew install pyenv"
        exit 1
    fi
fi

echo "✅ pyenv가 설치되어 있습니다."
echo ""

# pyenv 초기화
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# 필요한 Python 버전 확인
REQUIRED_PYTHON="3.9"
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
    echo "📌 필요한 Python 버전: $PYTHON_VERSION"

    # 해당 버전이 설치되어 있는지 확인
    if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
        echo "⚠️  Python ${PYTHON_VERSION}이(가) 설치되지 않았습니다."
        echo ""
        read -p "Python ${PYTHON_VERSION}을(를) 자동으로 설치하시겠습니까? (y/n): " -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📥 Python ${PYTHON_VERSION} 설치 중... (시간이 걸릴 수 있습니다)"
            pyenv install ${PYTHON_VERSION}

            if [ $? -eq 0 ]; then
                echo "✅ Python ${PYTHON_VERSION} 설치 완료"
            else
                echo "❌ Python ${PYTHON_VERSION} 설치 실패"
                exit 1
            fi
        else
            echo "📝 다음 명령어로 수동 설치하세요:"
            echo "  pyenv install ${PYTHON_VERSION}"
            exit 1
        fi
    else
        echo "✅ Python ${PYTHON_VERSION}이(가) 이미 설치되어 있습니다."
    fi
else
    echo "⚠️  .python-version 파일이 없습니다."
    echo "📝 기본 Python 버전(3.9.20)을 설정합니다."
    echo ""
    read -p "Python 3.9.20을 설치하고 설정하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Python 3.9.20이 설치되어 있는지 확인
        if ! pyenv versions --bare | grep -q "^3.9.20$"; then
            echo "📥 Python 3.9.20 설치 중... (시간이 걸릴 수 있습니다)"
            pyenv install 3.9.20

            if [ $? -ne 0 ]; then
                echo "❌ Python 3.9.20 설치 실패"
                exit 1
            fi
        fi

        # .python-version 파일 생성
        echo "3.9.20" > .python-version
        echo "✅ Python 3.9.20 설정 완료"
        PYTHON_VERSION="3.9.20"
    else
        echo "📝 다음 명령어로 Python 버전을 설정하세요:"
        echo "  pyenv install 3.9.20"
        echo "  pyenv local 3.9.20"
        exit 1
    fi
fi

# Python 경로 설정
PYTHON_BIN="$(pyenv which python)"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "⚠️  Python을 찾을 수 없습니다."
    exit 1
fi

echo "🐍 Python 버전: $($PYTHON_BIN --version)"
echo "📍 Python 경로: $PYTHON_BIN"
echo ""

# Infisical CLI 설치 확인
echo "🔐 Checking Infisical CLI..."
if ! command -v infisical &> /dev/null; then
    echo "⚠️  Infisical CLI가 설치되지 않았습니다."
    echo "📝 Infisical CLI 설치 방법:"
    echo "  - macOS: brew install infisical/infisical-cli/infisical"
    echo "  - 기타: https://infisical.com/docs/cli/overview"
    echo ""
    exit 1
fi

# Infisical 로그인 확인
echo "🔐 Checking Infisical authentication..."
if ! infisical run --env=dev --path=/backend -- echo "check" </dev/null &> /dev/null; then
    echo "⚠️  Infisical에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  infisical login"
    echo ""
    exit 1
fi
echo "✅ Infisical authentication verified"
echo ""

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "📝 .env.example을 복사하여 .env 파일을 생성하세요:"
    echo "  cp .env.example .env"
    echo ""
    echo "  그 다음 .env 파일을 편집하여 로컬 환경 변수를 설정하세요."
    exit 1
fi

# .env 파일에서 환경 변수 로드
echo "🔑 환경 변수 로드 (.env)"
export $(grep -v '^#' .env | xargs)

if [ -n "$MYSQL_USER" ]; then
    echo "✓ .env 파일에서 MYSQL_USER를 로드했습니다."
fi
if [ -n "$MYSQL_PASSWORD" ]; then
    echo "✓ .env 파일에서 MYSQL_PASSWORD를 로드했습니다."
fi
if [ -n "$PORT" ]; then
    echo "✓ .env 파일에서 PORT를 로드했습니다."
fi
if [ -n "$SECRET_KEY" ]; then
    echo "✓ .env 파일에서 SECRET_KEY를 로드했습니다."
fi

# 기본값 설정
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_DATABASE=${MYSQL_DATABASE:-podpod_local}
PORT=${PORT:-8000}

echo ""

# MySQL 설치 확인
echo "🗄️  Checking MySQL..."

# Homebrew로 설치된 MySQL 확인
MYSQL_INSTALLED=false
if command -v mysql &> /dev/null; then
    MYSQL_INSTALLED=true
elif command -v brew &> /dev/null && brew list mysql &> /dev/null; then
    # Homebrew로 설치되었지만 PATH에 없는 경우
    MYSQL_INSTALLED=true
    # Homebrew MySQL 경로를 PATH에 추가
    export PATH="/opt/homebrew/opt/mysql/bin:$PATH"
    export PATH="/usr/local/opt/mysql/bin:$PATH"
fi

if [ "$MYSQL_INSTALLED" = false ]; then
    echo "⚠️  MySQL이 설치되지 않았습니다."
    echo ""

    if command -v brew &> /dev/null; then
        read -p "MySQL을 자동으로 설치하시겠습니까? (y/n): " -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📥 MySQL 설치 중..."
            brew install mysql

            if [ $? -eq 0 ]; then
                echo "✅ MySQL 설치 완료"
                # PATH 업데이트
                export PATH="/opt/homebrew/opt/mysql/bin:$PATH"
                export PATH="/usr/local/opt/mysql/bin:$PATH"
            else
                echo "❌ MySQL 설치 실패"
                exit 1
            fi
        else
            echo "📝 MySQL 수동 설치 방법:"
            echo "  brew install mysql"
            exit 1
        fi
    else
        echo "📝 MySQL 설치 방법:"
        echo "  - macOS: brew install mysql"
        echo "  - Ubuntu/Debian: sudo apt-get install mysql-server"
        exit 1
    fi
fi

echo "✅ MySQL이 설치되어 있습니다."
echo ""

# MySQL 실행 확인
echo "🔌 Checking if MySQL is running..."
if mysqladmin ping -h "$MYSQL_HOST" -P "$MYSQL_PORT" --silent 2>/dev/null; then
    echo "✅ MySQL is running"
else
    echo "⚠️  MySQL is not running"
    echo ""

    if command -v brew &> /dev/null && brew list mysql &> /dev/null; then
        read -p "MySQL 서비스를 자동으로 시작하시겠습니까? (y/n): " -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🚀 MySQL 서비스 시작 중..."
            brew services start mysql

            # MySQL이 시작될 때까지 대기
            echo "⏳ MySQL 서버가 시작될 때까지 대기 중..."
            sleep 5

            # 연결 확인
            if mysqladmin ping -h "$MYSQL_HOST" -P "$MYSQL_PORT" --silent 2>/dev/null; then
                echo "✅ MySQL이 성공적으로 시작되었습니다."
            else
                echo "❌ MySQL 시작에 실패했습니다."
                echo "📝 수동으로 시작하세요: brew services start mysql"
                exit 1
            fi
        else
            echo "📝 MySQL 서비스를 수동으로 시작하세요:"
            echo "  brew services start mysql"
            exit 1
        fi
    else
        echo "📝 MySQL 서비스를 시작하세요:"
        echo "  - macOS: brew services start mysql"
        echo "  - Linux: sudo systemctl start mysql"
        exit 1
    fi
fi

echo ""

# 데이터베이스 존재 확인
echo "🗄️  Checking database '$MYSQL_DATABASE'..."
if mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "USE $MYSQL_DATABASE" 2>/dev/null; then
    echo "✅ Database '$MYSQL_DATABASE' exists"
else
    echo "⚠️  Database '$MYSQL_DATABASE' does not exist"
    echo ""
    read -p "지금 데이터베이스를 생성하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "CREATE DATABASE $MYSQL_DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        if [ $? -eq 0 ]; then
            echo "✅ Database '$MYSQL_DATABASE' created successfully"
        else
            echo "❌ Failed to create database"
            exit 1
        fi
    else
        exit 1
    fi
fi

echo ""

# 기존 로컬 프로세스 확인 및 중지
echo "🔍 Checking local uvicorn processes..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "⚠️  로컬 uvicorn 프로세스가 실행 중입니다."
    echo "📝 포트 충돌을 방지하기 위해 프로세스를 중지합니다."
    echo ""

    echo "🛑 로컬 프로세스 중지 중..."
    pkill -f "uvicorn main:app"
    sleep 2

    # 종료 확인
    if pgrep -f "uvicorn main:app" > /dev/null; then
        echo "⚠️  프로세스 중지에 실패했습니다. 강제 종료를 시도합니다..."
        pkill -9 -f "uvicorn main:app"
        sleep 1
    fi

    echo "✅ 로컬 프로세스가 중지되었습니다."
else
    echo "✅ 로컬 uvicorn 프로세스가 실행 중이지 않습니다."
fi
echo ""

# 포트 사용 확인 (추가 안전장치)
echo "🔌 Checking port $PORT availability..."
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  포트 $PORT이(가) 사용 중입니다."
    echo "📝 포트를 사용 중인 프로세스를 중지합니다."

    # 포트를 사용 중인 프로세스 종료
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1

    echo "✅ 포트가 해제되었습니다."
else
    echo "✅ 포트 $PORT이(가) 사용 가능합니다."
fi
echo ""

# Docker 컨테이너 확인 및 중지
echo "🐳 Checking Docker containers..."
if command -v docker &> /dev/null; then
    # docker-compose.dev.yml의 컨테이너가 실행 중인지 확인
    if docker ps --format '{{.Names}}' | grep -q "podpod-api-dev\|podpod-mysql-dev"; then
        echo "⚠️  Docker 개발 환경 컨테이너가 실행 중입니다."
        echo "📝 포트 충돌을 방지하기 위해 컨테이너를 중지합니다."
        echo ""

        # docker-compose.dev.yml 파일이 있는지 확인
        if [ -f "docker-compose.dev.yml" ]; then
            echo "🛑 Docker 컨테이너 중지 중..."
            docker compose -f docker-compose.dev.yml down

            if [ $? -eq 0 ]; then
                echo "✅ Docker 컨테이너가 중지되었습니다."
            else
                echo "⚠️  Docker 컨테이너 중지에 실패했습니다."
                echo "📝 수동으로 중지하세요: docker compose -f docker-compose.dev.yml down"
            fi
        else
            # docker-compose 파일이 없으면 개별 컨테이너 중지
            echo "🛑 개별 컨테이너 중지 중..."
            docker stop podpod-api-dev podpod-mysql-dev 2>/dev/null
            docker rm podpod-api-dev podpod-mysql-dev 2>/dev/null
            echo "✅ 컨테이너가 중지되었습니다."
        fi
        echo ""
    else
        echo "✅ Docker 컨테이너가 실행 중이지 않습니다."
        echo ""
    fi
else
    echo "ℹ️  Docker가 설치되지 않았습니다. (선택사항)"
    echo ""
fi

# 가상환경 확인 및 생성
if [ ! -d ".venv" ]; then
    echo "📦 가상환경이 없습니다. 생성 중..."
    $PYTHON_BIN -m venv .venv
    if [ $? -eq 0 ]; then
        echo "✅ 가상환경 생성 완료"
    else
        echo "❌ 가상환경 생성 실패"
        exit 1
    fi
else
    echo "✅ 가상환경이 이미 존재합니다."
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
echo "📦 패키지 설치 확인 중..."
if [ ! -f ".venv/.installed" ]; then
    echo "📥 패키지 설치 중... (최초 1회)"
    pip install --upgrade pip
    pip install -r requirements.txt

    if [ $? -eq 0 ]; then
        echo "✅ 패키지 설치 완료"
        touch .venv/.installed
    else
        echo "❌ 패키지 설치 실패"
        exit 1
    fi
else
    echo "✅ 패키지가 이미 설치되어 있습니다."
    echo "💡 재설치하려면 .venv/.installed 파일을 삭제하세요."
fi

echo ""

# Alembic 마이그레이션
echo "🗄️  데이터베이스 마이그레이션"
read -p "Alembic 마이그레이션을 실행하시겠습니까? (y/n): " -r
echo
MIGRATION_SUCCESS=true
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Running Alembic migrations with Infisical..."
    infisical run --env=dev --path=/backend -- alembic upgrade head

    if [ $? -eq 0 ]; then
        echo "✅ 마이그레이션 완료"
    else
        echo "❌ 마이그레이션 실패"
        MIGRATION_SUCCESS=false
    fi
fi

# 마스터 데이터 import 확인
echo ""
if [ "$MIGRATION_SUCCESS" = false ]; then
    echo "⚠️  마이그레이션이 실패하여 마스터 데이터 import를 건너뜁니다."
fi

if [ "$MIGRATION_SUCCESS" = true ] && [ -f "seeds/master_data.sql" ]; then
    read -p "마스터 데이터를 import하시겠습니까? (seeds/master_data.sql) (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 Importing master data..."

        # 기존 마스터 데이터 삭제
        echo "🗑️  기존 마스터 데이터 삭제 중..."
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
            SET FOREIGN_KEY_CHECKS=0;
            TRUNCATE TABLE schedule_contents;
            TRUNCATE TABLE schedule_members;
            TRUNCATE TABLE artist_schedules;
            TRUNCATE TABLE artist_images;
            TRUNCATE TABLE artist_names;
            TRUNCATE TABLE artist_units;
            TRUNCATE TABLE artists;
            TRUNCATE TABLE locations;
            TRUNCATE TABLE tendency_results;
            TRUNCATE TABLE tendency_surveys;
            SET FOREIGN_KEY_CHECKS=1;
        " 2>&1 | grep -v "Warning"

        # 마스터 데이터 import
        mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < seeds/master_data.sql 2>&1 | grep -v "Warning"

        if [ $? -eq 0 ]; then
            echo "✅ 마스터 데이터 import 완료"
        else
            echo "❌ 마스터 데이터 import 실패"
        fi
    fi
else
    if [ ! -f "seeds/master_data.sql" ]; then
        echo "ℹ️  마스터 데이터 파일이 없습니다 (seeds/master_data.sql)"
        echo "   ./scripts/export-master-data.sh 를 실행하여 데이터를 추출하세요."
    fi
fi

echo ""

# Prometheus 실행 여부 확인
echo "📊 Prometheus 모니터링"
read -p "Prometheus를 함께 실행하시겠습니까? (y/n): " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Prometheus 설치 확인
    if ! command -v prometheus &> /dev/null; then
        echo "⚠️  Prometheus가 설치되지 않았습니다."
        echo ""

        if command -v brew &> /dev/null; then
            read -p "Prometheus를 자동으로 설치하시겠습니까? (y/n): " -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "📥 Prometheus 설치 중..."
                brew install prometheus

                if [ $? -eq 0 ]; then
                    echo "✅ Prometheus 설치 완료"
                else
                    echo "❌ Prometheus 설치 실패"
                    echo "📝 수동으로 설치하세요: brew install prometheus"
                fi
            fi
        else
            echo "📝 Prometheus 설치 방법:"
            echo "  - macOS: brew install prometheus"
            echo "  - Ubuntu/Debian: sudo apt-get install prometheus"
        fi
    fi

    # Prometheus 실행
    if command -v prometheus &> /dev/null; then
        # 기존 Prometheus 프로세스 확인
        if pgrep -f "prometheus.*prometheus.dev.yml" > /dev/null; then
            echo "⚠️  Prometheus가 이미 실행 중입니다."
            echo "🛑 기존 Prometheus 프로세스 중지 중..."
            pkill -f "prometheus.*prometheus.dev.yml"
            sleep 2
        fi

        echo "🚀 Prometheus 시작 중..."
        echo "📊 Prometheus URL: http://localhost:9090"

        # Prometheus를 백그라운드로 실행
        prometheus --config.file=prometheus.dev.yml > prometheus.log 2>&1 &
        PROMETHEUS_PID=$!

        echo "✅ Prometheus가 백그라운드로 실행되었습니다. (PID: $PROMETHEUS_PID)"
        echo "📝 로그: tail -f prometheus.log"
        echo ""

        # 종료 시 Prometheus도 함께 종료하도록 trap 설정
        trap "echo '🛑 Prometheus 중지 중...'; kill $PROMETHEUS_PID 2>/dev/null; exit" INT TERM
    fi
fi

echo ""
echo "=========================================="
echo "🎉 PodPod Backend 로컬 서버 시작"
echo "=========================================="
echo ""
echo "🌐 API URL: http://localhost:${PORT}"
echo "📚 API Docs: http://localhost:${PORT}/docs"
echo "📊 Metrics: http://localhost:${PORT}/metrics"
if command -v prometheus &> /dev/null && pgrep -f "prometheus.*prometheus.dev.yml" > /dev/null; then
    echo "📈 Prometheus: http://localhost:9090"
fi
echo ""
echo "💡 종료하려면 Ctrl+C를 누르세요."
echo ""

# CONFIG_FILE 환경변수 설정
export CONFIG_FILE="config.dev.yaml"

# uvicorn으로 서버 실행 (가상환경 + Infisical)
# Infisical에서 민감한 환경변수를 로드합니다
infisical run --env=dev --path=/backend -- python -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
