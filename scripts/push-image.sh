#!/bin/bash

# PodPod Backend - Docker Hub 이미지 푸시 스크립트

# 사용법 체크
if [ "$#" -ne 1 ]; then
    echo "사용법: $0 <environment>"
    echo "예시: $0 stg"
    echo "      $0 prod"
    exit 1
fi

ENV=$1

# 환경 검증
if [ "$ENV" != "stg" ] && [ "$ENV" != "prod" ]; then
    echo "❌ 올바르지 않은 환경입니다. 'stg' 또는 'prod'를 사용하세요."
    exit 1
fi

echo "🚀 Building and pushing Docker image for $ENV environment..."
echo ""

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker가 설치되지 않았습니다."
    echo "📝 Docker 설치 방법: https://docs.docker.com/get-docker/"
    echo ""
    exit 1
fi

# Docker Hub 로그인 확인
echo "🔐 Checking Docker Hub authentication..."
if ! docker info | grep -q "Username"; then
    echo "⚠️  Docker Hub에 로그인되어 있지 않습니다."
    echo "📝 다음 명령어로 로그인해주세요:"
    echo "  docker login"
    exit 1
fi

# Docker Hub 사용자명 입력 받기
read -p "Docker Hub 사용자명을 입력하세요: " DOCKER_USERNAME
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ Docker Hub 사용자명이 필요합니다."
    exit 1
fi

# 이미지 이름 및 태그 설정
IMAGE_NAME="podpod-backend"
IMAGE_TAG="${ENV}-$(date +%Y%m%d-%H%M%S)"
LATEST_TAG="${ENV}-latest"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}"

echo "📦 Image: ${FULL_IMAGE_NAME}:${IMAGE_TAG}"
echo "📦 Latest: ${FULL_IMAGE_NAME}:${LATEST_TAG}"
echo ""

# 이미지 빌드
echo "🔨 Building Docker image..."
docker build -t ${FULL_IMAGE_NAME}:${IMAGE_TAG} -t ${FULL_IMAGE_NAME}:${LATEST_TAG} .

if [ $? -ne 0 ]; then
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

echo "✅ Docker image built successfully!"
echo ""

# 빌드된 이미지 정보 표시
echo "📋 Built image information:"
docker images ${FULL_IMAGE_NAME}:${LATEST_TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 푸시 전 최종 확인
echo "⚠️  다음 이미지를 Docker Hub에 푸시하려고 합니다:"
echo "  - ${FULL_IMAGE_NAME}:${IMAGE_TAG}"
echo "  - ${FULL_IMAGE_NAME}:${LATEST_TAG}"
echo ""
read -p "계속하시겠습니까? (y/n): " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 푸시가 취소되었습니다."
    exit 0
fi

# Docker Hub에 푸시
echo "📤 Pushing to Docker Hub..."
docker push ${FULL_IMAGE_NAME}:${IMAGE_TAG}
docker push ${FULL_IMAGE_NAME}:${LATEST_TAG}

if [ $? -ne 0 ]; then
    echo "❌ Docker Hub 푸시 실패"
    exit 1
fi

echo ""
echo "✅ Successfully pushed to Docker Hub!"
echo ""
echo "📋 이미지 정보:"
echo "  - ${FULL_IMAGE_NAME}:${IMAGE_TAG}"
echo "  - ${FULL_IMAGE_NAME}:${LATEST_TAG}"
echo ""
echo "📝 서버에서 실행하려면:"
echo "  ./scripts/start-${ENV}.sh"
echo ""
