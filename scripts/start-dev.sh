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
if ! infisical run --env=dev --path=/backend -- echo "check" &> /dev/null; then
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

# 로그 확인
echo ""
echo "✅ Containers are starting..."
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
