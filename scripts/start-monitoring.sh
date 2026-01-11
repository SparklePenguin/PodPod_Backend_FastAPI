#!/bin/bash

# PodPod Backend - Prometheus 모니터링 시작 스크립트

echo "📊 Starting Prometheus Monitoring..."
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.." || exit 1
PROJECT_ROOT=$(pwd)

echo "📁 프로젝트 경로: $PROJECT_ROOT"
echo ""

# Prometheus 설치 확인
echo "🔍 Checking Prometheus..."
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
                exit 1
            fi
        else
            echo "📝 Prometheus 수동 설치 방법:"
            echo "  brew install prometheus"
            exit 1
        fi
    else
        echo "📝 Prometheus 설치 방법:"
        echo "  - macOS: brew install prometheus"
        echo "  - Ubuntu/Debian: sudo apt-get install prometheus"
        exit 1
    fi
fi

echo "✅ Prometheus가 설치되어 있습니다."
echo ""

# Prometheus 설정 파일 확인
CONFIG_FILE="prometheus.dev.yml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️  Prometheus 설정 파일을 찾을 수 없습니다: $CONFIG_FILE"
    exit 1
fi

echo "📋 설정 파일: $CONFIG_FILE"
echo ""

# 기존 Prometheus 프로세스 확인
echo "🔍 Checking existing Prometheus processes..."
if pgrep -f "prometheus.*prometheus.dev.yml" > /dev/null; then
    echo "⚠️  Prometheus가 이미 실행 중입니다."
    echo ""
    read -p "기존 프로세스를 중지하고 다시 시작하시겠습니까? (y/n): " -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 기존 Prometheus 프로세스 중지 중..."
        pkill -f "prometheus.*prometheus.dev.yml"
        sleep 2

        # 종료 확인
        if pgrep -f "prometheus.*prometheus.dev.yml" > /dev/null; then
            echo "⚠️  프로세스 중지에 실패했습니다. 강제 종료를 시도합니다..."
            pkill -9 -f "prometheus.*prometheus.dev.yml"
            sleep 1
        fi

        echo "✅ 기존 프로세스가 중지되었습니다."
    else
        echo "📝 기존 프로세스가 계속 실행됩니다."
        exit 0
    fi
else
    echo "✅ 실행 중인 Prometheus 프로세스가 없습니다."
fi

echo ""
echo "=========================================="
echo "🚀 Prometheus 시작"
echo "=========================================="
echo ""
echo "📊 Prometheus URL: http://localhost:9090"
echo "📈 Targets: http://localhost:9090/targets"
echo ""
echo "💡 종료하려면 Ctrl+C를 누르세요."
echo ""

# 종료 시 Prometheus도 함께 종료하도록 trap 설정
cleanup() {
    echo ""
    echo "🛑 Prometheus 중지 중..."
    pkill -f "prometheus.*prometheus.dev.yml"
    exit 0
}

trap cleanup INT TERM

# Prometheus를 포그라운드로 실행 (로그를 직접 볼 수 있도록)
prometheus --config.file=prometheus.dev.yml
