#!/bin/bash

# PodPod Backend - 개발 환경 실행 스크립트

echo "🚀 Starting PodPod Backend (Development Environment)..."
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
if ! infisical run --env=dev --path=/backend -- echo "check" </dev/null &> /dev/null; then
    echo "⚠️  Infisical에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  infisical login"
    exit 1
fi

# 기존 컨테이너 정리 (선택사항)
echo "🧹 Cleaning up old containers..."
infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml down

# 컨테이너 빌드 및 실행
echo "🔨 Building and starting containers with Infisical..."
infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml up --build -d

# 컨테이너가 시작될 때까지 대기
echo ""
echo "⏳ Waiting for database to be ready..."
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
    docker exec podpod-api-dev alembic -c database/alembic.ini upgrade head

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

        # Infisical에서 MYSQL_PASSWORD 가져오기
        MYSQL_PASSWORD=$(infisical secrets get MYSQL_PASSWORD --env=dev --path=/backend --plain)

        if [ -z "$MYSQL_PASSWORD" ]; then
            echo "❌ MYSQL_PASSWORD를 Infisical에서 가져올 수 없습니다."
        else
            # 기존 마스터 데이터 삭제
            echo "🗑️  기존 마스터 데이터 삭제 중..."
            docker exec podpod-mysql-dev mysql -u root -p"$MYSQL_PASSWORD" podpod_dev -e "
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
            docker exec -i podpod-mysql-dev mysql -u root -p"$MYSQL_PASSWORD" podpod_dev < seeds/master_data.sql 2>&1 | grep -v "Warning"

            if [ $? -eq 0 ]; then
                echo "✅ 마스터 데이터 import 완료"
            else
                echo "❌ 마스터 데이터 import 실패"
            fi
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
echo "  - View logs:        infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml logs -f"
echo "  - View app logs:    infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml logs -f app"
echo "  - View db logs:     infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml logs -f db"
echo "  - Stop containers:  infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml down"
echo "  - Restart:          infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml restart"
echo ""
echo "🌐 API URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

# 로그 자동 표시 (선택사항 - Ctrl+C로 종료)
read -p "로그를 실시간으로 보시겠습니까? (y/n): " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    infisical run --env=dev --path=/backend -- docker-compose -f docker-compose.dev.yml logs -f
fi
