#!/bin/bash

# PodPod Backend - 프로덕션 환경 실행 스크립트

echo "🚀 Starting PodPod Backend (Production Environment)..."
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
if ! infisical run --env=prod --path=/backend -- echo "check" </dev/null &> /dev/null; then
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

# 프로덕션 배포 확인
echo "⚠️  프로덕션 환경에 배포하려고 합니다."
read -p "계속하시겠습니까? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ 배포가 취소되었습니다."
    exit 0
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
docker stop podpod-api-prod 2>/dev/null || true
docker rm podpod-api-prod 2>/dev/null || true

# 최신 이미지 pull
echo "📥 Pulling latest image from Docker Hub..."
docker pull ${DOCKER_USERNAME}/podpod-backend:prod-latest

if [ $? -ne 0 ]; then
    echo "❌ Docker 이미지 pull 실패"
    echo "📝 먼저 이미지를 빌드하고 푸시해주세요:"
    echo "  ./scripts/push-image.sh prod"
    exit 1
fi

# 이미지 정보 확인
echo ""
echo "📋 Downloaded image information:"
docker images ${DOCKER_USERNAME}/podpod-backend:prod-latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 최종 배포 확인
read -p "이 이미지로 프로덕션에 배포하시겠습니까? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ 배포가 취소되었습니다."
    exit 0
fi

# 컨테이너 실행
echo "🔨 Starting containers with Infisical..."
infisical run --env=prod --path=/backend -- docker-compose -p podpod-prod -f docker-compose.prod.yml up -d

# 헬스체크
echo ""
echo "🏥 Waiting for health check..."
sleep 10

# 컨테이너 상태 확인
if infisical run --env=prod --path=/backend -- docker-compose -p podpod-prod -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅ Production deployment successful!"
else
    echo "❌ Deployment failed. Check logs:"
    echo "   infisical run --env=prod --path=/backend -- docker-compose -p podpod-prod -f docker-compose.prod.yml logs"
    exit 1
fi

echo ""
echo "📋 Useful commands:"
echo "  - View logs:        infisical run --env=prod --path=/backend -- docker-compose -p podpod-prod -f docker-compose.prod.yml logs -f"
echo "  - Stop containers:  infisical run --env=prod --path=/backend -- docker-compose -p podpod-prod -f docker-compose.prod.yml down"
echo "  - Restart:          infisical run --env=prod --path=/backend -- docker-compose -p podpod-prod -f docker-compose.prod.yml restart"
echo ""
echo "🌐 API URL: https://sp-podpod.com"
echo "📚 API Docs: https://sp-podpod.com/docs"
echo ""
