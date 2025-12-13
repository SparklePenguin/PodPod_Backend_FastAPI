#!/bin/bash

# PodPod Backend - 스테이징 환경 실행 스크립트

echo "🚀 Starting PodPod Backend (Staging Environment)..."
echo ""

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker가 설치되지 않았습니다."
    echo "📝 Docker 설치 방법: https://docs.docker.com/get-docker/"
    echo ""
    exit 1
fi

# Docker Compose 확인 (docker compose 또는 docker-compose)
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "⚠️  Docker Compose가 설치되지 않았습니다."
    echo "📝 Docker Compose 설치 방법: https://docs.docker.com/compose/install/"
    echo ""
    exit 1
fi

# Infisical CLI 설치 확인
if ! command -v infisical &> /dev/null; then
    echo "⚠️  Infisical CLI가 설치되지 않았습니다."
    echo "📝 Infisical CLI 설치 방법: https://infisical.com/docs/cli/overview"
    echo ""
    exit 1
fi

# Infisical 로그인 확인
echo "🔐 Checking Infisical authentication..."
if ! infisical run --env=staging --path=/backend -- echo "check" </dev/null &> /dev/null; then
    echo "⚠️  Infisical에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  infisical login"
    exit 1
fi

# Docker Hub 로그인 확인
echo "🔐 Checking Docker Hub authentication..."
if [ ! -f "$HOME/.docker/config.json" ] || ! grep -q "auths" "$HOME/.docker/config.json" 2>/dev/null; then
    echo "⚠️  Docker Hub에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  docker login"
    exit 1
fi

# Docker Hub 사용자명 입력
read -p "Docker Hub 사용자명을 입력하세요: " DOCKER_USERNAME
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ Docker Hub 사용자명이 필요합니다."
    exit 1
fi

export DOCKER_USERNAME

# 기존 컨테이너 정리 (DOCKER_USERNAME 사용하지 않음)
echo "🧹 Cleaning up old containers..."
docker stop podpod-api-stg 2>/dev/null || true
docker rm podpod-api-stg 2>/dev/null || true

# 최신 이미지 pull
echo "📥 Pulling latest image from Docker Hub..."
docker pull ${DOCKER_USERNAME}/podpod-backend:stg-latest

if [ $? -ne 0 ]; then
    echo "❌ Docker 이미지 pull 실패"
    echo "📝 먼저 이미지를 빌드하고 푸시해주세요:"
    echo "  ./scripts/push-image.sh stg"
    exit 1
fi

# 이미지 정보 확인
echo ""
echo "📋 Downloaded image information:"
docker images ${DOCKER_USERNAME}/podpod-backend:stg-latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 배포 확인
read -p "이 이미지로 배포하시겠습니까? (y/n): " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 배포가 취소되었습니다."
    exit 0
fi

# 컨테이너 실행
echo "🔨 Starting containers with Infisical..."
infisical run --env=staging --path=/backend -- docker-compose -p podpod-stg -f docker-compose.stg.yml up -d

# 컨테이너가 시작될 때까지 대기
echo ""
echo "⏳ Waiting for application to be ready..."
sleep 5

# DB 초기화 확인
echo ""
echo "🗄️  데이터베이스 초기화"
echo ""
read -p "Alembic 마이그레이션을 실행하시겠습니까? (테이블 생성) (y/n): " -r
echo
MIGRATION_SUCCESS=true
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Running Alembic migrations..."
    docker exec podpod-api-stg alembic upgrade head

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
    echo "❌ 스크립트를 종료합니다."
    exit 1
fi

if [ -f "seeds/master_data.sql" ]; then
    read -p "마스터 데이터를 import하시겠습니까? (seeds/master_data.sql) (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 Importing master data..."

        # DB 접속 정보 입력
        echo ""
        echo "MySQL 접속 정보를 입력하세요:"
        read -p "Host (기본: localhost): " DB_HOST
        DB_HOST=${DB_HOST:-localhost}

        read -p "Port (기본: 3306): " DB_PORT
        DB_PORT=${DB_PORT:-3306}

        read -p "Database (기본: podpod_staging): " DB_NAME
        DB_NAME=${DB_NAME:-podpod_staging}

        read -p "User (기본: root): " DB_USER
        DB_USER=${DB_USER:-root}

        read -sp "Password: " DB_PASSWORD
        echo ""
        echo ""

        # 기존 마스터 데이터 삭제
        echo "🗑️  기존 마스터 데이터 삭제 중..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
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
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < seeds/master_data.sql 2>&1 | grep -v "Warning"

        if [ $? -eq 0 ]; then
            echo "✅ 마스터 데이터 import 완료"
        else
            echo "❌ 마스터 데이터 import 실패"
        fi
    fi
else
    echo "ℹ️  마스터 데이터 파일이 없습니다 (seeds/master_data.sql)"
    echo "   ./scripts/export-master-data.sh 를 실행하여 데이터를 추출하세요."
fi

# 로그 확인
echo ""
echo "✅ Containers are running..."
echo ""
echo "📋 Useful commands:"
echo "  - View logs:        infisical run --env=staging --path=/backend -- docker-compose -p podpod-stg -f docker-compose.stg.yml logs -f"
echo "  - Stop containers:  infisical run --env=staging --path=/backend -- docker-compose -p podpod-stg -f docker-compose.stg.yml down"
echo "  - Restart:          infisical run --env=staging --path=/backend -- docker-compose -p podpod-stg -f docker-compose.stg.yml restart"
echo ""
echo "🌐 API URL: https://sp-podpod.com/stg"
echo "📚 API Docs: https://sp-podpod.com/stg/docs"
echo ""

# 로그 자동 표시 (선택사항 - Ctrl+C로 종료)
read -p "로그를 실시간으로 보시겠습니까? (y/n): " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    infisical run --env=staging --path=/backend -- docker-compose -p podpod-stg -f docker-compose.stg.yml logs -f
fi
