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
if ! infisical run --env=staging --path=/backend -- echo "check" &> /dev/null; then
    echo "⚠️  Infisical에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  infisical login"
    exit 1
fi

# Docker Hub 사용자명 입력
read -p "Docker Hub 사용자명을 입력하세요: " DOCKER_USERNAME
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ Docker Hub 사용자명이 필요합니다."
    exit 1
fi

export DOCKER_USERNAME

# 기존 컨테이너 정리
echo "🧹 Cleaning up old containers..."
infisical run --env=staging --path=/backend -- docker-compose -f docker-compose.stg.yml down

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
infisical run --env=staging --path=/backend -- docker-compose -f docker-compose.stg.yml up -d

# 로그 확인
echo ""
echo "✅ Containers are starting..."
echo ""
echo "📋 Useful commands:"
echo "  - View logs:        infisical run --env=staging --path=/backend -- docker-compose -f docker-compose.stg.yml logs -f"
echo "  - Stop containers:  infisical run --env=staging --path=/backend -- docker-compose -f docker-compose.stg.yml down"
echo "  - Restart:          infisical run --env=staging --path=/backend -- docker-compose -f docker-compose.stg.yml restart"
echo ""
echo "🌐 API URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"      
echo ""

# 로그 자동 표시 (선택사항 - Ctrl+C로 종료)
read -p "로그를 실시간으로 보시겠습니까? (y/n): " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    infisical run --env=staging --path=/backend -- docker-compose -f docker-compose.stg.yml logs -f
fi
